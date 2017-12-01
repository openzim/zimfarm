import os
from flask import send_from_directory


def serve_static(path):
    if not os.path.exists('static/{}'.format(path)):
        path = 'index.html'
    return send_from_directory('static', path)