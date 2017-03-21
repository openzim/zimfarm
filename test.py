from api.database import SQLiteDB
from api.status import TaskStatus
import datetime
db = SQLiteDB()
db.add_task(("a", 0, datetime.datetime.now()))