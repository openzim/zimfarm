FROM python:3.8-buster

WORKDIR /usr/src

COPY task-requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app
RUN ln -s /usr/src/app/task_worker.py /usr/local/bin/task-worker
RUN chmod +x /usr/local/bin/task-worker

ENV WEB_API_URI https://api.farm.openzim.org/v1
ENV WORKDIR /data
VOLUME /var/run/docker.sock
VOLUME /data

CMD ["task-worker"]
