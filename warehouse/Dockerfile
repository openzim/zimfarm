FROM python:latest

WORKDIR /usr/src
COPY ./app /usr/src/app

RUN pip3 install -r ./app/requirements.txt
RUN mkdir /zim_files
RUN ssh-keygen -t rsa -N "" -f server.key

ENV RSA_KEY server.key
ENV PORT 22
ENV ROOT_PATH /zim_files
ENV LOG_PATH /warehouse.log

EXPOSE 22

ENTRYPOINT ["python3", "app/main.py"]