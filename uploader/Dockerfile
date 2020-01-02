FROM python:3.8-buster

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install humanfriendly==4.18

COPY uploader.py /usr/local/bin/uploader
RUN chmod +x /usr/local/bin/uploader
RUN touch /usr/share/marker

CMD ["uploader"]
