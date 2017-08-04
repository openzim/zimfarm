FROM tiangolo/uwsgi-nginx-flask:python3.6

# install requirements
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# copy flask app
COPY ./app /app

ENTRYPOINT python /app/main.py