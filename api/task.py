import json
from .database import SQLiteDB


def get_tasks():
    db = SQLiteDB()
    tasks = db.get_tasks()
    return json.dumps(tasks)