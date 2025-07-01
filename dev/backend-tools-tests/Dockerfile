FROM python:3.13-alpine

RUN apk add --no-cache openssl gcc libffi-dev libc-dev openssh-keygen && \
    rm -rf /var/cache/apk/* && \
    pip install --no-cache-dir -U pip

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY tests /app/tests

RUN cd /app && \
    pip install .[dev]

WORKDIR /app/
