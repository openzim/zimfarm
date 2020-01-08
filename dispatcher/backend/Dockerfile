FROM rgaudin/uwsgi-nginx:python3.8

RUN pip install -U pip
RUN pip install uwsgi==2.0.18

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY src /app/
COPY docs /app/docs
WORKDIR /app/

ENV DOCS_DIR /app/docs
ENV MONGODB_URI mongodb://localhost
ENV SOCKET_URI tcp://localhost:5000
ENV INIT_PASSWORD admin

# from uwsgi-nginx
ENV UWSGI_INI /app/uwsgi.ini
ENV UWSGI_CHEAPER 2
ENV UWSGI_PROCESSES 16
ENV NGINX_MAX_UPLOAD 0
ENV NGINX_WORKER_PROCESSES 1
ENV LISTEN_PORT 80
ENV NGINV_ENABLE_GZIP 1

# prestart script (former entrypoint - database init)
COPY prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

# periodic tasks as a supervisor listenner (every minute)
COPY supervisor-listener.py /usr/local/bin/supervisor-listener
RUN chmod +x /usr/local/bin/supervisor-listener
COPY periodic.conf /etc/supervisor/conf.d/periodic.conf
