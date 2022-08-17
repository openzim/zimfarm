FROM rgaudin/uwsgi-nginx:python3.8
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir uwsgi==2.0.18

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/
COPY docs /app/docs
WORKDIR /app/

ENV DOCS_DIR /app/docs
ENV MONGODB_URI mongodb://localhost
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

# mailgun for notifications
ENV MAILGUN_API_URL https://api.mailgun.net/v3/mg.farm.openzim.org
ENV MAILGUN_FROM Zimfarm <info@farm.openzim.org>
# ENV MAILGUN_API_KEY -

# slack for notifications
# ENV SLACK_URL -
# ENV SLACK_USERNAME zimfarm
# ENV SLACK_EMOJI :ghost:
# ENV SLACK_ICON https://farm.openzim.org/assets/apple-touch-icon.png

# GLOBAL NOTIFICATIONS
# format: list of `method,target,target` separated by comma `,`
# multiple notification for same event separated with pipe `|`
# ENV suffixed with event: `GLOBAL_NOTIFICATION_started` or `GLOBAL_NOTIFICATION_ended`
# ENV GLOBAL_NOTIFICATION_ended slack,#zimfarm-events,@rgaudin|mailgun,reg@kiwix.org


# prestart script (former entrypoint - database init)
COPY prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

# periodic tasks as a supervisor listenner (every minute)
COPY supervisor-listener.py /usr/local/bin/supervisor-listener
RUN chmod +x /usr/local/bin/supervisor-listener
COPY periodic.conf /etc/supervisor/conf.d/periodic.conf
