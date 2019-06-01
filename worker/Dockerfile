FROM python:3.7

RUN apt-get update
RUN apt-get -y install sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /usr/src

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app

RUN groupadd -r docker
RUN groupadd -r zim
RUN adduser --disabled-password --gecos "" celery_runner
RUN usermod -aG root,sudo,docker,zim celery_runner

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN chown -R celery_runner /usr/src

ENV USERNAME username
ENV PASSWORD password
ENV NODE_NAME default_node_name
ENV QUEUES celery

ENV DISPATCHER_HOST farm.openzim.org
ENV RABBIT_PORT 5671
ENV WAREHOUSE_HOST warehouse.farm.openzim.org
ENV WAREHOUSE_PORT 1522

USER celery_runner

ENTRYPOINT ["/entrypoint.sh"]
