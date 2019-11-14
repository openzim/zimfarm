FROM debian:bullseye-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ssh curl python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN /usr/bin/curl -V

COPY uploader.py /usr/local/bin/uploader
RUN chmod +x /usr/local/bin/uploader

CMD ["uploader"]
