#!/bin/sh

(
    sleep 10; \
    rabbitmqctl delete_user guest; \
    rabbitmqctl add_vhost zimfarm; \

    rabbitmqctl add_user admin $ADMIN_PASSWORD; \
    rabbitmqctl set_user_tags admin administrator; \
    rabbitmqctl set_permissions -p zimfarm admin ".*" ".*" ".*"; \

    rabbitmqctl add_user $DISPATCHER_USERNAME $DISPATCHER_PASSWORD; \
    rabbitmqctl set_user_tags $DISPATCHER_USERNAME administrator; \
    rabbitmqctl set_permissions -p zimfarm $DISPATCHER_USERNAME ".*" ".*" ".*"; \

) & rabbitmq-server $@