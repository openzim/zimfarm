FROM python:latest

COPY . /usr/src/worker
WORKDIR /usr/src/worker

RUN pip3 install -r ./requirements.txt

ENTRYPOINT ["python", "docker_entry.py"]
