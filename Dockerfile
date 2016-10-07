FROM python:3
# RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev

ADD requirements.txt /tmp/requirements.txt
ADD test-requirements.txt /tmp/test-requirements.txt

RUN pip install \
	-r /tmp/requirements.txt \
	-r /tmp/test-requirements.txt \
 && rm /tmp/requirements.txt /tmp/test-requirements.txt

WORKDIR /code
