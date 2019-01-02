FROM python:3.6

WORKDIR /usr/src
COPY ./app /usr/src/app

RUN pip3 install -r ./app/requirements.txt

ENV USERNAME username
ENV PASSWORD password
ENV HOSTNAME default_hostname

ENV DISPATCHER_HOST farm.openzim.org
ENV RABBIT_PORT 5671
ENV WAREHOUSE_HOST warehouse.farm.openzim.org
ENV WAREHOUSE_PORT 1522

ENTRYPOINT ["python", "app/main.py"]
