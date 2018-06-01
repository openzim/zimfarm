FROM tiangolo/uwsgi-nginx:python3.6

COPY nginx.conf /etc/nginx/conf.d/
COPY src /usr/src/flask
COPY static /usr/src/static

RUN pip install -r /usr/src/flask/requirements.txt

ENV UWSGI_INI /usr/src/flask/uwsgi.ini
WORKDIR /usr/src/flask

RUN chmod +x ./start.sh
CMD ["./start.sh"]