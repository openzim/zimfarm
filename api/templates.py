import json
from flask import request
from .database import SQLiteDB


def list():
    if request.method != 'GET': return None
    db = SQLiteDB()
    templates = db.get_templates()
    return json.dumps(templates)

def create():
    return '{"message": "under construction"}'

def update():
    return '{"message": "under construction"}'