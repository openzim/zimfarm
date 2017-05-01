FROM python:3.5

# install requirements
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# start worker
COPY ./app /flower
WORKDIR /flower
ENTRYPOINT flower -A tasks --port=5555