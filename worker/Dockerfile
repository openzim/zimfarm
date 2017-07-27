FROM python:latest

WORKDIR /usr/src
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt


RUN chmod +x init.sh
ENTRYPOINT ["./init.sh"]