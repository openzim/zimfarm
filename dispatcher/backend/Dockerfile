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
ENV MONGODB_URI mongodb://localhost
ENV SOCKET_URI tcp://localhost:5000
ENV INIT_PASSWORD admin

ENTRYPOINT ["entrypoint.sh"]

COPY uwsgi.ini /etc/uwsgi.ini
CMD ["uwsgi", "--ini", "/etc/uwsgi.ini"]
