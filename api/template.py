import json
from flask import request
from .database import SQLiteDB


def template():
    if request.method == 'GET':
        db = SQLiteDB()
        templates = db.get_templates()
        return json.dumps(templates)
