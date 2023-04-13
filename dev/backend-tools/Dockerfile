FROM python:3.8-bullseye
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN pip install --no-cache-dir -U pip

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install black flake8 isort

COPY src /app/
COPY docs /app/docs
WORKDIR /app/