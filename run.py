#/usr/bin/env python
import nipype.pipeline.engine as pe
from nipype import config as ncfg
from nipype.interfaces import ants
import argparse
from bids.grabbids import BIDSLayout
from spynoza.hires.workflows import init_hires_unwarping_wf
from spynoza.io.bids import DerivativesDataSink
import os
import os.path as op

parser = argparse.ArgumentParser(description='Docker image to run ANTS registrations')
parser.add_argument('bids_dir', action='store',
                    help='the root folder of a BIDS valid dataset (sub-XXXXX folders should '
                         'be found at the top level in this folder).')

parser.add_argument('output_dir', action='store',
                    help='the output path for the outcomes of preprocessing and visual '  )

parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant'])
parser.add_argument('--task', 
                    default=None,
                    help='Task to use')
parser.add_argument('--method',
                    default='topup',
                    help='Mask for fixed image')
parser.add_argument('--use_one_fieldmap_for_all_runs',
                    default='topup',
                    help='Mask for fixed image')
parser.add_argument('--n_procs',
                    default=4,
                    type=int,
                    help='Number of threads to use for workflow.')
parser.add_argument('--num_threads_ants',
                    default=4,
                    type=int,
                    help='Number of threads to use for ants threads.')
parser.add_argument('-w', '--work-dir', action='store', default='work',
                         help='path where intermediate results should be stored')
parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                        'corresponds to sub-<participant_label> from the BIDS spec '
                        '(so it does not include "sub-"). If this parameter is not '
                        'provided all subjects should be analyzed. Multiple '
                        'participants can be specified with a space separated list.',
                    type=str)
parser.add_argument('--linear_registration_parameters', help='ANTS registration preset to use '
                    '(in spynoza/data/ants_json) for linear registration.',
                    type=str,
                    default='linear_hires.json',
                    nargs=1)
parser.add_argument('--nonlinear_registration_parameters', help='ANTS registration preset to use '
                    '(in spynoza/data/ants_json) for non-linear registration.',
                    type=str,
                    default='nonlinear_precise.json',
                    nargs=1)
parser.add_argument('--init_reg_file', default=None, help='One or more .lta-matrices that can init the'
                    'registration from EPI to T1w-space')
parser.add_argument('--crop_bold_epis', default=True, help='Temporally crop BOLD EPIs to'
                    'size of OP EPIs.')
parser.add_argument('--topup_package',
                    help='Which implementation of TOPUP to use.',
                    default='afni',
                    choices=['afni', 'fsl'])
parser.add_argument('--no_within_epi_reg',
                    action='store_false',
                    dest='within_epi_reg',
                    default=True,
                    help='Whether to register BOLD EPIs to each other after'
                    'registration to T1-weighted space',)
parser.add_argument('--polish',
                    action='store_true',
                    dest='polish',
                    default=False,
                    help='Whether to polish BOLD EPIs using non-linear regitration'
                    'to T1-weighted space',)

opts = parser.parse_args()


layout = BIDSLayout('/data')

output_dir = op.abspath(opts.output_dir)
log_dir = op.join(output_dir, 'logs')
work_dir = op.abspath(opts.work_dir)

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)
os.makedirs(work_dir, exist_ok=True)

# Nipype config (logs and execution)
ncfg.update_config({
    'logging': {'log_directory': log_dir, 'log_to_file': True},
    'execution': {'crashdump_dir': log_dir, 'crashfile_format': 'txt'},
})


if opts.task is None:
    task = layout.get_tasks()[0]
else:
    task = opts.task
    print(task)
print(opts.participant_label)

bold_epis = layout.get('file', subject=opts.participant_label, type='bold', extensions=['.nii', '.nii.gz'], task=task)
print("Using the following %d BOLD EPIs:" % len(bold_epis))
for b_epi in bold_epis:
    print(" * %s" % b_epi)

if opts.method == 'topup':
    epi_op = [layout.get_fieldmap(b_epi)['epi'] for b_epi in bold_epis]
    print("Using following %d runs for op EPI:" % len(epi_op))
    for fn in epi_op:
        print(" * %s" % fn)
else:
    epi_op = None

if opts.method == 't1w_epi':
    t1w_epi = layout.get('file', type='T1w', subject=opts.participant_label)
    t1w_epi = [fn for fn in t1w_epi if 'epi' in fn.lower()][0]
    print("Using %s as T1-weighted EPI!" % t1w_epi)

    inv2_epi = layout.get('file', type='INV2', subject=opts.participant_label)
    inv2_epi = [fn for fn in inv2_epi if 'epi'  in fn.lower()][0]
    print("Using %s as INV2 EPI" % inv2_epi)
else:
    t1w_epi = None
    inv2_epi = None

t1w = layout.get('file', type='T1w')
t1w = [fn for fn in t1w if 'epi' not in fn.lower()][0]
print("using %s as T1w-weighted structural image" % t1w)

wf = init_hires_unwarping_wf(name="unwarp_hires",
                            method=opts.method,
                            bids_layout=layout,
                            single_warpfield=opts.use_one_fieldmap_for_all_runs,
                            register_to='last',
                            init_reg_file=opts.init_reg_file,
                            linear_registration_parameters=opts.linear_registration_parameters,
                            nonlinear_registration_parameters=opts.nonlinear_registration_parameters,
                            bold_epi=bold_epis,
                            epi_op=epi_op,
                            t1w_epi=t1w_epi,
                            t1w=t1w,
                            inv2_epi=inv2_epi,
                            crop_bold_epis=opts.crop_bold_epis,
                            topup_package=opts.topup_package,
                            within_epi_reg=opts.within_epi_reg,
                            num_threads_ants=opts.num_threads_ants,
                            polish=opts.polish)
    
wf.base_dir = work_dir

ds_epi_to_t1w_transformed = pe.MapNode(DerivativesDataSink(base_directory='/out',
                                          suffix='epi_to_t1w'),
                              iterfield=['source_file', 'in_file'],
                      name='ds_epi_to_t1w_transformed')
ds_epi_to_t1w_transformed.inputs.source_file = bold_epis
wf.connect(wf.get_node('outputspec'), 'mean_epi_in_T1w_space', ds_epi_to_t1w_transformed, 'in_file')

ds_epi_to_t1w_transforms = pe.MapNode(DerivativesDataSink(base_directory='/out',
                                          suffix='epi_to_t1w'),
                              iterfield=['source_file', 'in_file'],
                      name='ds_epi_to_t1w_transforms')
ds_epi_to_t1w_transforms.inputs.source_file = bold_epis
wf.connect(wf.get_node('outputspec'), 'bold_epi_to_T1w_transforms', ds_epi_to_t1w_transforms, 'in_file')

wf.run(plugin='MultiProc', plugin_args={'n_procs':opts.n_procs})
