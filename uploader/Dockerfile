FROM python:3.13-slim-bookworm
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir "humanfriendly==10.0" "kiwixstorage==0.9.0"

COPY openzim_uploader/__init__.py /usr/local/bin/uploader
RUN chmod +x /usr/local/bin/uploader
RUN touch /usr/share/marker

ENV HOST_KNOW_FILE /etc/ssh/known_hosts
ENV MARKER_FILE /usr/share/marker
ENV SCP_BIN_PATH /usr/bin/scp
ENV SFTP_BIN_PATH /usr/bin/sftp

CMD ["uploader"]
