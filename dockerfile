FROM python:3.6
ADD requirements.txt /app/requirements.txt
ADD ./celery_rabbitmq_test/ /app/
WORKDIR /app/
RUN pip install -r requirements.txt
ENTRYPOINT celery -A test_celery worker --loglevel=info