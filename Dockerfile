FROM python:3

ADD requirements.txt /tmp/requirements.txt
ADD test-requirements.txt /tmp/test-requirements.txt

RUN pip install \
    -r /tmp/requirements.txt \
    -r /tmp/test-requirements.txt \
 && rm /tmp/requirements.txt /tmp/test-requirements.txt

RUN useradd -ms /bin/bash pg_bawler
USER pg_bawler

WORKDIR /opt/pg_bawler
