FROM docker:17.06.0


RUN apk add --update python3 python3-dev py3-pip  build-base

# install requirements
COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

# start worker
COPY ./app /celery_worker
WORKDIR /celery_worker
ENTRYPOINT celery -A tasks worker --loglevel=info