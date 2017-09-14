FROM phusion/baseimage:0.9.19
ENV ANTSPATH=/usr/lib/ants
RUN mkdir $ANTSPATH
RUN curl -sSL "https://dl.dropbox.com/s/f3rvpefq9oq65ki/ants.tar.gz" \
    | tar -xzC $ANTSPATH --strip-components 2

RUN buildDeps='cmake build-essential git zlib1g-dev python3-dev' \
    && apt-get update \
    && apt-get install -y $buildDeps --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* 

RUN apt-get update \
    && apt-get install -y --no-install-recommends --auto-remove git curl unzip \
    && curl -o anaconda.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash anaconda.sh -b -p /opt/anaconda && rm -f anaconda.sh

RUN /opt/anaconda/bin/pip install nipype

ENV CONDA_PATH "/opt/anaconda"
ENV PATH $CONDA_PATH/bin:$ANTSPATH:$PATH

RUN mkdir -p /code
COPY run.py /code/run.py
COPY ants_json /ants_json

RUN chmod +x /code/run.py
ENTRYPOINT ["/opt/anaconda/bin/python", "/code/run.py"]
