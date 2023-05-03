import boto3
import logging
import os
import pathlib

from flask import Flask, Response, make_response, redirect, render_template
from flask_cors import CORS

from routes import (
    API_PATH,
    auth,
    errors,
    languages,
    offliners,
    platforms,
    requested_tasks,
    schedules,
    tags,
    tasks,
    users,
    workers,
)
from utils.broadcaster import BROADCASTER
from utils.database import Initializer
from utils.json import ZimfarmJsonProvider

# TEMP fix awaiting kiwixstorage
boto3.set_stream_logger("", logging.CRITICAL)

if os.getenv("DOCS_DIR"):
    docs_dir = pathlib.Path(os.getenv("DOCS_DIR")).resolve()
else:
    # docs dir outside codebase
    docs_dir = pathlib.Path(__file__).parent.resolve().parent.joinpath("docs")
application = Flask(__name__, template_folder=docs_dir)
application.json = ZimfarmJsonProvider(application)
CORS(application)

logging.basicConfig(
    level=logging.DEBUG, format="[%(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@application.route(f"{API_PATH}/openapi.yaml")
def openapi():
    fname = "openapi_v1.yaml"
    if not docs_dir.joinpath(fname).exists():
        return Response("Zimfarm API (OpenAPI spec missing)")
    resp = make_response(render_template(fname))
    resp.headers["Content-Type"] = "application/yaml"
    return resp


@application.route(f"{API_PATH}")
def api_doc():
    fname = "swagger-ui.html"
    if not docs_dir.joinpath(fname).exists():
        return Response("Zimfarm API (documentation missing)")
    return render_template(fname)


@application.route("/")
def home():
    return redirect("/v1")


application.register_blueprint(auth.Blueprint())
application.register_blueprint(schedules.Blueprint())
application.register_blueprint(tasks.Blueprint())
application.register_blueprint(requested_tasks.Blueprint())
application.register_blueprint(users.Blueprint())
application.register_blueprint(workers.Blueprint())
application.register_blueprint(languages.Blueprint())
application.register_blueprint(tags.Blueprint())
application.register_blueprint(offliners.Blueprint())
application.register_blueprint(platforms.Blueprint())

errors.register_handlers(application)

logger.info(f"connected broadcaster to {BROADCASTER.uri}")
BROADCASTER.broadcast_dispatcher_started()


if __name__ == "__main__":
    Initializer.check_if_schema_is_up_to_date()
    Initializer.create_initial_user()
    application.run(
        host=os.getenv("BINDING_HOST", "localhost"),
        debug=os.getenv("DEBUG", False),
        port=int(os.getenv("BINDING_PORT", 8000)),
        threaded=True,
    )
