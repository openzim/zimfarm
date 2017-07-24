FROM docker:17.06.0
VOLUME /var/run/docker.sock:/var/run/docker.sock

WORKDIR /usr/src
COPY . .

RUN apk add --update python3 python3-dev py3-pip build-base
RUN pip3 install --no-cache-dir -r requirements.txt

RUN adduser -S -g docker zimfarm_worker 
USER zimfarm_worker

ENTRYPOINT ["python3", "app/main.py"]
