FROM tiangolo/uwsgi-nginx:python3.6

COPY nginx.conf /etc/nginx/conf.d/
COPY requirements.txt /usr/src/
COPY src /usr/src/flask
COPY static /usr/src/static

RUN pip install -r /usr/src/requirements.txt

ENV UWSGI_INI /usr/src/flask/uwsgi.ini
WORKDIR /usr/src/flask

RUN chmod +x ./start.sh
CMD ["./start.sh"]