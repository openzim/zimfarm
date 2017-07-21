#!/bin/sh

(
    sleep 10; \
    rabbitmqctl delete_user guest; \
    rabbitmqctl add_vhost zimfarm; \

    rabbitmqctl add_user $DISPATCHER_USERNAME $DISPATCHER_PASSWORD; \
    rabbitmqctl set_user_tags $DISPATCHER_USERNAME administrator; \
    rabbitmqctl set_permissions -p zimfarm $DISPATCHER_USERNAME ".*" ".*" ".*"; \

    rabbitmqctl add_user $ADMIN_USERNAME $ADMIN_PASSWORD; \
    rabbitmqctl set_user_tags $ADMIN_USERNAME administrator; \
    rabbitmqctl set_permissions -p zimfarm $ADMIN_USERNAME ".*" ".*" ".*"; \

) & rabbitmq-server $@