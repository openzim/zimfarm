from flask import request
from . import flask, get_db
from .response import JSONResponse


@flask.route('/templates/list', methods=['GET'])
def list():
    db = get_db()
    templates = db.get_templates()
    return JSONResponse(templates)


@flask.route('/templates/create', methods=['POST'])
def create():
    return JSONResponse({
        "message": "under construction"
    })


@flask.route('/templates/update', methods=['POST'])
def update():
    return JSONResponse({
        "message": "under construction"
    })
