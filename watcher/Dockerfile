FROM python:3.10-alpine

LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apk update && apk --no-cache add wget

ENV DOWNLOAD_URL https://archive.org/download/stackexchange/
ENV ZIMFARM_API_URL https://api.farm.openzim.org/v1
ENV ZIMFARM_USERNAME ""
ENV ZIMFARM_PASSWORD ""
ENV S3_URL ""

RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -U pip && pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY watcher.py /usr/local/bin/watcher
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/watcher /usr/local/bin/entrypoint

ENTRYPOINT ["entrypoint"]
CMD ["watcher", "-h"]
