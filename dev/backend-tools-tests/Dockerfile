FROM python:3.13-slim-bookworm

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/zimfarm_backend/__about__.py /app/src/zimfarm_backend/__about__.py
RUN pip install --no-cache-dir "/app[dev]"

COPY src /app/src
COPY tests /app/tests

RUN pip install --no-cache-dir /app

WORKDIR /app/
