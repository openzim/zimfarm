FROM python:3.8-buster

WORKDIR /usr/src

COPY manager-requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app
RUN ln -s /usr/src/app/worker_manager.py /usr/local/bin/worker-manager
RUN chmod +x /usr/local/bin/worker-manager

ENV WEB_API_URI https://api.farm.openzim.org/v1
ENV SOCKET_URI tcp://tcp.farm.openzim.org:32029
ENV WORKDIR /data
VOLUME /var/run/docker.sock
VOLUME /data

CMD ["worker-manager"]
