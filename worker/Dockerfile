FROM python:latest

WORKDIR /usr/src
COPY zimfarmworker ./zimfarmworker
COPY requirements.txt ./zimfarmworker/requirements.txt

RUN pip3 install -r ./zimfarmworker/requirements.txt

ENTRYPOINT ["python", "-m", "zimfarmworker", "--dockerized"]
