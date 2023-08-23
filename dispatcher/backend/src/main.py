import os
import time

# import boto3
from flask import Flask

application = Flask(__name__)


@application.route("/")
def home():
    time.sleep(10)
    return "HELLO"


if __name__ == "__main__":
    application.run(
        host=os.getenv("BINDING_HOST", "localhost"),
        debug=os.getenv("DEBUG", False),
        port=int(os.getenv("BINDING_PORT", 8000)),
        threaded=True,
    )
