FROM nginx:latest 

COPY ./dist /var/www/html

RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf /etc/nginx/