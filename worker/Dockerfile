FROM python:latest

WORKDIR /usr/src
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN useradd zimfarm_worker
RUN usermod -a -G staff zimfarm_worker

ENTRYPOINT ["python3", "app/main.py"]