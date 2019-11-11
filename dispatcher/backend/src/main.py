import os
import logging

from flask import Flask, Response
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


app = Flask(__name__)
app.json_encoder = Encoder
cors = CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
logger.addHandler(handler)

@app.route("/")
def home():
    return Response("zimfarm API")


app.register_blueprint(auth.Blueprint())
app.register_blueprint(schedules.Blueprint())
app.register_blueprint(tasks.Blueprint())
app.register_blueprint(requested_tasks.Blueprint())
app.register_blueprint(users.Blueprint())
app.register_blueprint(workers.Blueprint())
app.register_blueprint(languages.Blueprint())
app.register_blueprint(tags.Blueprint())

errors.register_handlers(app)

logger.info(f"connected broadcaster to {BROADCASTER.uri}")
BROADCASTER.broadcast_dispatcher_started()


if __name__ == "__main__":
    Initializer.create_initial_user()
    app.run(host="0.0.0.0", debug=os.getenv("DEBUG", False), port=80, threaded=True)
