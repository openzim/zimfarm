FROM rgaudin/uwsgi-nginx:python3.8
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir uwsgi==2.0.18

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/
COPY docs /app/docs
COPY maint-scripts /app/maint-scripts
WORKDIR /app/

ENV DOCS_DIR /app/docs
ENV SOCKET_URI tcp://localhost:5000
ENV INIT_PASSWORD admin

# from uwsgi-nginx
ENV UWSGI_INI /app/uwsgi.ini
ENV UWSGI_CHEAPER 4
ENV UWSGI_CHEAPER_STEP 2
ENV UWSGI_PROCESSES 32
ENV NGINX_MAX_UPLOAD 0
ENV NGINX_WORKER_PROCESSES 1
ENV LISTEN_PORT 80
ENV NGINV_ENABLE_GZIP 1

