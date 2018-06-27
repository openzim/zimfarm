FROM python:latest

WORKDIR /usr/src
COPY ./app /usr/src/app

RUN pip3 install -r ./app/requirements.txt

ENTRYPOINT ["python3", "app/main.py"]
