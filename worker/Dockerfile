FROM python:3.7

WORKDIR /usr/src

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app

ENV USERNAME username
ENV PASSWORD password
ENV NODE_NAME default_node_name
ENV QUEUES celery

ENV DISPATCHER_HOST farm.openzim.org
ENV RABBIT_PORT 5671
ENV WAREHOUSE_HOST warehouse.farm.openzim.org
ENV WAREHOUSE_PORT 1522

ENTRYPOINT ["python", "app/main.py"]
