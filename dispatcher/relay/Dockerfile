FROM python:3.8-buster

RUN pip install -U pip zmq

COPY relay.py /usr/local/bin/zimfarm-relay

EXPOSE 5000
ENV INTERNAL_SOCKET_PORT "5000"
ENV SOCKET_PORT "6000"
ENV BIND_TO_IP "y"
ENV EVENTS "requested-task,requested-tasks,cancel-task,task-event,dispatcher-started,worker-checkin"

CMD ["zimfarm-relay"]
