#/usr/bin/env python
print('yo')
import nipype.pipeline.engine as pe
from nipype.interfaces import ants
import argparse

parser = argparse.ArgumentParser(
    description='Docker image to run ANTS registrations')
parser.add_argument('moving_image', help='The image to be transformed')
parser.add_argument('fixed_image', help='The image to register to.')
parser.add_argument('--moving_image_mask', help='Mask for moving image')
parser.add_argument('--fixed_image_mask', help='Mask for fixed image')
parser.add_argument('--json_file',
                    default='linear_precise.json',
                    help='JSON-file to use for ANTS parameters')
parser.add_argument('--n_threads', help='Number of threads to use.')

args = parser.parse_args()

wf = pe.Workflow('polish_nonlinear')

moving_image = '/data/%s' % args.moving_image
fixed_image = '/data/%s' % args.fixed_image

json_pars = '/ants_json/%s' % args.json_file
reg = pe.Node(ants.Registration(from_file=json_pars),
              name='reg')

if args.moving_image_mask:
    reg.inputs.moving_image_masks = '/data/%s' % args.moving_image_mask

else:
    moving_image_mask = None

if args.fixed_image_mask:
    reg.inputs.fixed_image_masks = '/data/%s' % args.fixed_image_mask
else:
    fixed_image_mask = None

reg.inputs.moving_image = moving_image
reg.inputs.fixed_image = fixed_image

reg.inputs.output_warped_image = True



reg.base_directory = '/data'
reg.run()
