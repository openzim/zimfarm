FROM python:3.8-buster

RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime
RUN echo "UTC" > /etc/timezone

RUN pip install -U pip zmq

COPY relay.py /usr/local/bin/zimfarm-relay

EXPOSE 5000
ENV INTERNAL_SOCKET_PORT "5000"
ENV SOCKET_PORT "6000"
ENV EVENTS "requested-task,requested-tasks,cancel-task,task-event,dispatcher-started"

CMD ["zimfarm-relay"]
