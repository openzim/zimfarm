from flask import request
from .database import SQLiteDB
from .response import JSONResponse


def list():
    if request.method != 'GET': return None
    db = SQLiteDB()
    templates = db.get_templates()
    return JSONResponse(templates)


def create():
    return JSONResponse({
        "message": "under construction"
    })


def update():
    return JSONResponse({
        "message": "under construction"
    })
