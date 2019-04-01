FROM python:3.7

WORKDIR /usr/src

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app

ENTRYPOINT ["python3", "app/main.py"]
