import os
import sys
import urllib.error
from time import sleep
from flask import Flask
from werkzeug.security import generate_password_hash
from cerberus import Validator

from routes import serve_static, auth, task, user, errors
from utils.json import Encoder
from utils.mongo import Database, Users


flask = Flask(__name__)
flask.json_encoder = Encoder

flask.route('/', methods=['GET'], defaults={'path': 'index.html'})(serve_static)
flask.route('/<path:path>', methods=['GET'])(serve_static)

flask.register_blueprint(auth.blueprint)
flask.register_blueprint(task.blueprint)

errors.register_handlers(flask)


if __name__ == "__main__":
    # TODO: check mandatory env
    is_debug = os.getenv('DEBUG', False)
    init_username = os.getenv('INIT_USERNAME', 'admin')
    init_password = os.getenv('INIT_PASSWORD', 'admin_pass')

    # initialization
    Database().initialize()
    users = Users()
    if users.find_one() is None:
        # create initial user in database
        document = {
            'username': init_username,
            'password_hash': generate_password_hash(init_password),
            'is_admin': True
        }
        validator = Validator(Users.schema)
        if not validator.validate(document):
            sys.exit()
        users.insert_one(document)

        # create initial user in database rabbitmq
        retries = 0
        while retries < 20:
            try:
                retries += 1
                user.update_rabbitmq_user(init_username, init_password)
                break
            except urllib.error.URLError:
                sleep(5)
        else:
            raise errors.RabbitMQError()


    # run flask app and serve requests
    flask.run(host='0.0.0.0', debug=is_debug, port=80)
