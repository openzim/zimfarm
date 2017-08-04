import os
from flask import Blueprint, jsonify, send_from_directory


blueprint = Blueprint('file', __name__, url_prefix='/file')
path = '/mnt/zimfarm_output'


@blueprint.route("", methods=["GET"])
def list():
    content = os.listdir(path)
    return jsonify(content)


@blueprint.route('/<string:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(directory=path, filename=filename)
