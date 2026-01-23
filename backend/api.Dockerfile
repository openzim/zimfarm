#syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/openzim/zimfarm
LABEL zimfarm=true

ENV INIT_PASSWORD=admin
# mailgun for notifications
ENV MAILGUN_API_URL=https://api.mailgun.net/v3/mg.farm.openzim.org
ENV ALEMBIC_UPGRADE_HEAD_ON_START=false
ENV MAILGUN_FROM="Zimfarm <info@farm.openzim.org>"
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

# - curl needed for healthcheck
# - zimscraperlib: We only install the binaries needed to make zimscraperlib image manipulation work, not
# the whole list as recommended on the installation page. This is because the installing all
# the prerequisites binaries blow up the image size by over 1Gb and we don't need all those
# functionalities.
RUN apt-get update && apt-get install -y curl libmagic1 wget \
    libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev libcairo2-dev \
    libharfbuzz-dev libfribidi-dev libxcb1-dev && \
    rm -rf /var/lib/apt/lists/*

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/zimfarm_backend/__about__.py /app/src/zimfarm_backend/__about__.py
RUN pip install --no-cache-dir /app[api]

# Copy all the files except the background_tasks directory since it is a different service
COPY --exclude=**/background_tasks src /app/src

RUN pip install --no-cache-dir /app  \
    && rm -rf /app/src \
    && rm /app/pyproject.toml \
    && rm /app/README.md


EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost/v2/healthcheck || exit 1

CMD ["uvicorn", "zimfarm_backend.api.entrypoint:app", "--host", "0.0.0.0", "--port", "80"]
