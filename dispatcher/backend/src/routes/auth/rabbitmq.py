import os
import random
import string

from flask import request, Response
from werkzeug.security import check_password_hash

from common.mongo import Users

system_username = 'system'
system_password = os.getenv('SYSTEM_PASSWORD',
                            ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)]))


def auth(intention: str):
    """
    Handles RabbitMQ auth http backend request
    See also: https://github.com/rabbitmq/rabbitmq-auth-backend-http
    See also: https://www.rabbitmq.com/management.html
    """

    username = request.form.get('username', None)
    if username is None:
        return Response('deny')

    if intention == 'user':
        password = request.form.get('password')
        if username == system_username and password == system_password:
            return Response('allow')
        else:
            user = Users().find_one({'username': username}, {'_id': 0, 'password_hash': 1, 'scope.rabbitmq': 1})
            if user is None:
                return Response('deny')
            password_hash = user.get('password_hash', '')
            tags = user.get('scope', {}).get('rabbitmq', [])
            if user is not None and check_password_hash(password_hash, password):
                tags = ['allow'] + tags
                return Response(' '.join(tags))
            else:
                return Response('deny')
    elif intention == 'vhost' or intention == 'resource' or intention == 'topic':
        vhost = request.form.get('vhost', None)
        if vhost != 'zimfarm':
            return Response('deny')

        if username == system_username:
            return Response('allow')
        else:
            user = Users().find_one({'username': username}, {'_id': 1})
            return Response('allow' if user is not None else 'deny')
    else:
        return Response('deny')
