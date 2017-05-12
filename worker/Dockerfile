FROM openzim/mwoffliner:latest


RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential

# install requirements
COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

# start worker
COPY ./app /celery_worker
WORKDIR /celery_worker
ENTRYPOINT service redis-server restart && celery -A tasks worker --loglevel=info