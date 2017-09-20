FROM phusion/baseimage:0.9.19
ENV ANTSPATH=/usr/lib/ants
RUN mkdir $ANTSPATH
RUN curl -sSL "https://dl.dropbox.com/s/f3rvpefq9oq65ki/ants.tar.gz" \
    | tar -xzC $ANTSPATH --strip-components 2

COPY docker/files/neurodebian.gpg /root/.neurodebian.gpg

RUN buildDeps='cmake build-essential git zlib1g-dev python3-dev curl unzip' \
    && apt-get update \
    && apt-get install -y $buildDeps --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*  \
    && curl -sSL http://neuro.debian.net/lists/xenial.us-ca.full >> /etc/apt/sources.list.d/neurodebian.sources.list \
    && apt-key add /root/.neurodebian.gpg \
    && (apt-key adv --refresh-keys --keyserver hkp://ha.pool.sks-keyservers.net 0xA5D32F012649A5A9 || true) \
    && apt-get update

RUN curl -o anaconda.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash anaconda.sh -b -p /opt/anaconda && rm -f anaconda.sh

ENV CONDA_PATH "/opt/anaconda"
ENV PATH $CONDA_PATH/bin:$ANTSPATH:$PATH

# Install AFNI/FSL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    fsl-core=5.0.9-4~nd16.04+1 \
                    afni=16.2.07~dfsg.1-5~nd16.04+1
ENV FSLDIR=/usr/share/fsl/5.0 \
    FSLOUTPUTTYPE=NIFTI_GZ \
    FSLMULTIFILEQUIT=TRUE \
    POSSUMDIR=/usr/share/fsl/5.0 \
    LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH \
    FSLTCLSH=/usr/bin/tclsh \
    FSLWISH=/usr/bin/wish \
    AFNI_MODELPATH=/usr/lib/afni/models \
    AFNI_IMSAVE_WARNINGS=NO \
    AFNI_TTATLAS_DATASET=/usr/share/afni/atlases \
    AFNI_PLUGINPATH=/usr/lib/afni/plugins

RUN pip install https://github.com/Gilles86/nipype/archive/ants_compose_multitransform.zip \
    && pip install nilearn \
    && pip install sklearn \
    && pip install bids \
    && pip install bottleneck \
    && pip install https://github.com/spinoza-centre/spynoza/archive/7t_hires.zip 

ENV PATH=/usr/lib/fsl/5.0:/usr/lib/afni/bin:$PATH

COPY ants_json /ants_json

RUN mkdir -p /code
COPY run.py /code/run.py
#RUN chmod +x /code/run.py
ENTRYPOINT ["/opt/anaconda/bin/python", "/code/run.py"]
