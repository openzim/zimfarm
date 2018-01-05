import os
from flask import send_file


def angular(path):
    file_path = os.path.join('static', path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    else:
        index_path = os.path.join('static', 'index.html')
        return send_file(index_path)