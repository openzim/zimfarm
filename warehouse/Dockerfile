FROM python:latest

WORKDIR /usr/src

COPY ./app/requirements.txt /usr/src/app/requirements.txt

RUN pip3 install -r ./app/requirements.txt
RUN mkdir /files
RUN ssh-keygen -t rsa -N "" -f server.key

ENV RSA_KEY server.key
ENV PORT 22
ENV ROOT_PATH /files
ENV LOG_PATH /warehouse.log

EXPOSE 22

COPY ./app /usr/src/app

ENTRYPOINT ["python3", "app/main.py"]
