FROM python:3.6
ADD . /celery_worker
WORKDIR /celery_worker
RUN pip install -r requirements.txt
ENTRYPOINT celery -A tasks worker --loglevel=info