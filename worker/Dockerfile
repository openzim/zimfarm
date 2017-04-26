FROM python:3.6

# install requirements
WORKDIR /
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# start worker
COPY ./app /celery_worker
WORKDIR /celery_worker
ENTRYPOINT celery worker -A tasks --loglevel=info