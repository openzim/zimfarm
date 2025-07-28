FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm
LABEL zimfarm=true

ENV INIT_PASSWORD admin
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

# curl needed for healthcheck
RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# prestart script (former entrypoint - database init)
COPY prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

# Copy periodic-scheduler and periodic-tasks for supervisor listener
COPY periodic-scheduler.py /app/periodic-scheduler.py
RUN chmod +x /app/periodic-scheduler.py

COPY periodic-tasks.py /app/periodic-tasks.py
RUN chmod +x /app/periodic-tasks.py

# periodic tasks as a supervisor listenner (every minute)
COPY supervisor-listener.py /usr/local/bin/supervisor-listener
RUN chmod +x /usr/local/bin/supervisor-listener

COPY periodic.conf /etc/supervisor/conf.d/periodic.conf

COPY maint-scripts /app/maint-scripts

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/zimfarm_backend/__about__.py /app/src/zimfarm_backend/__about__.py
RUN pip install --no-cache-dir /app

COPY src /app/src

RUN pip install --no-cache-dir /app  \
    && rm -rf /app/src \
    && rm /app/pyproject.toml \
    && rm /app/README.md


EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost/v2/healthcheck || exit 1

CMD ["uvicorn", "zimfarm_backend.main:app", "--host", "0.0.0.0", "--port", "80"]
