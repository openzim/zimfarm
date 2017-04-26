FROM tiangolo/uwsgi-nginx-flask:flask-python3.5

# install requirements
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

# copy flask app
COPY ./app /app
