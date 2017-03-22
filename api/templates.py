from flask import request
from . import app
from .database import SQLiteDB
from .response import JSONResponse
from celery import current_app


@app.route('/templates/list', methods=['GET'])
def list():
    db = SQLiteDB()
    templates = db.get_templates()
    return JSONResponse(templates)


@app.route('/templates/create', methods=['POST'])
def create():
    return JSONResponse({
        "message": "under construction"
    })


@app.route('/templates/update', methods=['POST'])
def update():
    return JSONResponse({
        "message": "under construction"
    })
