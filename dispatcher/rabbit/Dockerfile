FROM rabbitmq:3.7
RUN rabbitmq-plugins enable rabbitmq_auth_backend_http
RUN rabbitmq-plugins enable rabbitmq_auth_backend_cache

COPY ./rabbitmq.conf /etc/rabbitmq/rabbitmq.conf