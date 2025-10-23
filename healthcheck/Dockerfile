FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm
LABEL zimfarm true

# install Python dependencies first (since they change more rarely than src code)
COPY pyproject.toml README.md /app/
COPY src/healthcheck/__about__.py /app/src/healthcheck/__about__.py
RUN pip install --no-cache-dir /app

COPY src /app/src

RUN pip install --no-cache-dir /app  \
    && rm -rf /app/src \
    && rm /app/pyproject.toml \
    && rm /app/README.md


EXPOSE 80

CMD ["uvicorn", "healthcheck.main:app", "--host", "0.0.0.0", "--port", "80"]
