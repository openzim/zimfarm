from os import getenv
from time import sleep
import urllib.error
import jwt

import app
from routes import auth, user, task, file
from routes.error import exception, handler

app.flask.register_blueprint(auth.blueprint)
app.flask.register_blueprint(user.blueprint)
app.flask.register_blueprint(task.blueprint)
app.flask.register_blueprint(file.blueprint)


app.flask.errorhandler(exception.InvalidRequest)(handler.invalid_request)
app.flask.errorhandler(exception.UsernameNotValid)(handler.username_not_valid)
app.flask.errorhandler(exception.ScopeNotValid)(handler.scope_not_valid)
app.flask.errorhandler(jwt.DecodeError)(handler.jwt_decode_error)
app.flask.errorhandler(jwt.ExpiredSignatureError)(handler.jwt_expired)
app.flask.errorhandler(exception.NotEnoughPrivilege)(handler.not_enough_privilege)
app.flask.errorhandler(exception.AuthFailed)(handler.auth_failed)
app.flask.errorhandler(exception.UserDoesNotExist)(handler.user_does_not_exist)
app.flask.errorhandler(exception.TaskDoesNotExist)(handler.task_does_not_exist)
app.flask.errorhandler(exception.UserAlreadyExists)(handler.user_already_exists)
app.flask.errorhandler(exception.RabbitMQError)(handler.rabbitmq_error)
app.flask.errorhandler(exception.RabbitMQPutUserFailed)(handler.rabbitmq_put_user_failed)
app.flask.errorhandler(exception.RabbitMQDeleteUserFailed)(handler.rabbitmq_delete_user_failed)


def initialize():
    from werkzeug.security import generate_password_hash
    import mongo

    def create_rabbit_init_user(username, password):
        number_of_tries = 100
        while number_of_tries:
            try:
                number_of_tries -= 1
                user.update_rabbitmq_user(username, password)
                break
            except urllib.error.URLError:
                sleep(5)
        else:
            raise Exception()

    mongo.ZimfarmDatabase().initialize()
    users = mongo.UsersCollection()
    if users.find_one() is None:
        username = getenv('INIT_USERNAME', 'admin')
        password = getenv('INIT_PASSWORD', 'admin_pass')
        users.insert_one({
            'username': username,
            'password_hash': generate_password_hash(password),
            'scope': {'admin': True}
        })
        create_rabbit_init_user(username, password)


if __name__ == "__main__":
    isDebug = getenv('DEBUG', False)
    initialize()
    app.flask.run(host='0.0.0.0', debug=isDebug, port=80)
