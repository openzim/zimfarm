FROM python:3.8-slim-buster

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime
RUN echo "UTC" > /etc/timezone

RUN pip install -U pip
RUN pip install uwsgi==2.0.18

COPY requirements.txt /usr/src/
RUN pip install -r /usr/src/requirements.txt

COPY src /usr/src/
WORKDIR /usr/src/

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]

CMD ["uwsgi", "--master", "--processes", "5", "--http", ":80", \
     "--module", "main:app", "--buffer-size", "65535", \
     "--logformat", "[%(ctime)] %(addr) %(method) %(uri) => %(rsize) bytes in %(msecs) msecs (%(proto) %(status))"]
