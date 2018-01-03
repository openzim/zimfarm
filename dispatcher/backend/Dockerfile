FROM tiangolo/uwsgi-nginx-flask:python3.6

WORKDIR /app

# copy flask app
COPY . .

# install requirements
RUN pip install -r ./requirements.txt

ENTRYPOINT python ./main.py