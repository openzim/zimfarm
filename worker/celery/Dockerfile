FROM python:latest

WORKDIR /usr/src
COPY ./app /usr/src/app
COPY ./requirements.txt /usr/src/requirements.txt

RUN pip3 install -r ./requirements.txt

RUN useradd zimfarm_worker

ENTRYPOINT ["python3", "app/main.py"]

