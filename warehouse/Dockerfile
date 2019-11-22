FROM python:3.8-buster

WORKDIR /usr/src

COPY ./app/requirements.txt /usr/src/app/requirements.txt

RUN pip3 install -r ./app/requirements.txt
RUN mkdir /files
RUN ssh-keygen -t RSA -m PEM -N "" -f server.key

ENV RSA_KEY server.key
ENV PORT 22
ENV ROOT_PATH /files
ENV LOG_PATH /warehouse.log

EXPOSE 22

COPY ./app /usr/src/app

ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v1

ENTRYPOINT ["python3", "app/main.py"]
