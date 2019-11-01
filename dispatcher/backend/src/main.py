import os
import logging

from flask import Flask
from flask_cors import CORS

from routes import (
    auth,
    schedules,
    users,
    workers,
    languages,
    tags,
    errors,
    tasks,
    requested_tasks,
)
from utils.json import Encoder
from utils.database import Initializer
from utils.broadcaster import BROADCASTER


flask = Flask(__name__)
flask.json_encoder = Encoder
cors = CORS(flask, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
logger.addHandler(handler)

flask.register_blueprint(auth.Blueprint())
flask.register_blueprint(schedules.Blueprint())
flask.register_blueprint(tasks.Blueprint())
flask.register_blueprint(requested_tasks.Blueprint())
flask.register_blueprint(users.Blueprint())
flask.register_blueprint(workers.Blueprint())
flask.register_blueprint(languages.Blueprint())
flask.register_blueprint(tags.Blueprint())

errors.register_handlers(flask)

logger.info(f"connecter broadcaster to {BROADCASTER.uri}")


if __name__ == "__main__":
    Initializer.create_initial_user()
    flask.run(host="0.0.0.0", debug=os.getenv("DEBUG", False), port=80, threaded=True)
