#syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/openzim/zimfarm
LABEL zimfarm=true

ENV INIT_PASSWORD=admin
ENV ALEMBIC_UPGRADE_HEAD_ON_START=true

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/zimfarm_backend/__about__.py /app/src/zimfarm_backend/__about__.py

RUN pip install --no-cache-dir /app

# Copy all the files except the api since it is a different service
COPY --exclude=**/api src /app/src

RUN pip install --no-cache-dir /app  \
    && rm -rf /app/src \
    && rm /app/pyproject.toml \
    && rm /app/README.md

COPY maint-scripts /app/maint-scripts

CMD ["background-tasks"]
