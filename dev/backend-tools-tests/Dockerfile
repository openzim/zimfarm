FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y curl libmagic1 wget \
    libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev libcairo2-dev \
    libharfbuzz-dev libfribidi-dev libxcb1-dev && \
    rm -rf /var/lib/apt/lists/*

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/zimfarm_backend/__about__.py /app/src/zimfarm_backend/__about__.py
RUN pip install --no-cache-dir "/app[dev]"

COPY src /app/src
COPY tests /app/tests

RUN pip install --no-cache-dir /app

WORKDIR /app/
