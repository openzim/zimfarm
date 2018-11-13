FROM python:3.6

WORKDIR /usr/src
COPY ./app /usr/src/app

RUN pip3 install -r ./app/requirements.txt

ENV USERNAME automactic
ENV PASSWORD macOS10&open

ENV DISPATCHER_HOST farm.openzim.org
ENV RABBIT_PORT 5671
ENV WAREHOUSE_HOST farm.openzim.org
ENV WAREHOUSE_PORT 1522

ENV WORKING_DIR /Volumes/Data/zimfarm_working


ENTRYPOINT ["python", "app/main.py"]
