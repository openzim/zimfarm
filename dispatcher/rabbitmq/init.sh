#!/bin/sh

(
    sleep 10; \
    rabbitmqctl delete_user guest; \
    rabbitmqctl add_vhost zimfarm; \

    rabbitmqctl add_user $DISPATCHER_USERNAME $DISPATCHER_PASSWORD; \
    rabbitmqctl set_user_tags $DISPATCHER_USERNAME administrator; \
    rabbitmqctl set_permissions -p zimfarm $DISPATCHER_USERNAME ".*" ".*" ".*"; \

    rabbitmqctl add_user $INIT_USERNAME $INIT_PASSWORD; \
    rabbitmqctl set_user_tags $INIT_USERNAME worker; \
    rabbitmqctl set_permissions -p zimfarm $INIT_USERNAME ".*" ".*" ".*"; \

) & rabbitmq-server $@