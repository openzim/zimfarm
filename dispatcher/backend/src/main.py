import os
from flask import Flask

from routes import auth, schedules, users, workers, errors, tasks
from utils.json import Encoder
from prestart import Initializer


flask = Flask(__name__)
flask.json_encoder = Encoder

flask.register_blueprint(auth.Blueprint())
flask.register_blueprint(schedules.Blueprint())
flask.register_blueprint(tasks.Blueprint())
flask.register_blueprint(users.Blueprint())
flask.register_blueprint(workers.Blueprint())

errors.register_handlers(flask)


if __name__ == "__main__":
    Initializer.create_initial_user()

    is_debug = os.getenv('DEBUG', False)
    flask.run(host='0.0.0.0', debug=is_debug, port=80, threaded=True)
