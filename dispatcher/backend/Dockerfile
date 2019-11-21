FROM python:3.8-buster

RUN pip install -U pip
RUN pip install uwsgi==2.0.18

COPY requirements.txt /usr/src/
RUN pip install -r /usr/src/requirements.txt

COPY src /usr/src/
COPY docs /usr/src/docs
WORKDIR /usr/src/

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENV DOCS_DIR /usr/src/docs

ENTRYPOINT ["entrypoint.sh"]

CMD ["uwsgi", "--master", "--processes", "5", "--http", ":80", \
     "--module", "main:app", "--buffer-size", "65535", \
     "--logformat", "[%(ctime)] %(addr) %(method) %(uri) => %(rsize) bytes in %(msecs) msecs (%(proto) %(status))"]
