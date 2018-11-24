FROM python:3.6

WORKDIR /usr/src
COPY ./app /usr/src/app
COPY ./requirements.txt /usr/src/requirements.txt

RUN pip3 install -r ./requirements.txt

ENV MONGO_HOST localhost
ENV MONGO_PORT 27017

ENTRYPOINT ["python3", "app/main.py"]
