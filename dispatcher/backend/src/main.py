import os
from flask import Flask

from routes import auth, schedules, users, workers, errors
from utils.json import Encoder
from prestart import Initializer


flask = Flask(__name__)
flask.json_encoder = Encoder

flask.register_blueprint(auth.blueprint)
flask.register_blueprint(schedules.blueprint)
# flask.register_blueprint(task.blueprint)
flask.register_blueprint(users.Blueprint())
flask.register_blueprint(workers.blueprint)

errors.register_handlers(flask)


if __name__ == "__main__":
    Initializer.create_database_indexes()
    Initializer.create_initial_user()

    is_debug = os.getenv('DEBUG', False)
    flask.run(host='0.0.0.0', debug=is_debug, port=80, threaded=True)
