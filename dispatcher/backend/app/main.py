import os
import jwt
from werkzeug.security import generate_password_hash

import app
from routes import auth, user, task
from routes.error import exception, handler


app.flask.register_blueprint(auth.blueprint)
app.flask.register_blueprint(user.blueprint)
app.flask.register_blueprint(task.blueprint)


# error handler
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
    from database.models import User

    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin_pass')
    if User.query.filter_by(username=admin_username).first() is None:
        app.db.session.add(User(username=admin_username,
                                password_hash=generate_password_hash(admin_password),
                                scope='administrator'))
        app.db.session.commit()


    # mongo
    from database import mongo
    mongo.ZimfarmDatabase().initialize()

if __name__ == "__main__":
    isDebug = os.getenv('DEBUG', False)
    initialize()
    app.flask.run(host='0.0.0.0', debug=isDebug, port=80)
