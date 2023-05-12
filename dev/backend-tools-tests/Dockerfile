FROM python:3.8-alpine
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apk add --no-cache openssl gcc libffi-dev libc-dev openssh-keygen && \
    rm -rf /var/cache/apk/* && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir black flake8 isort
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt


COPY src /app/
COPY docs /app/docs
WORKDIR /app/
