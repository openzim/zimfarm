import os, sqlite3


class SQLiteDB:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)

        if not os.path.isfile(path):
            cursor = self._conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Task(
                Name text PRIMARY KEY,
                Type text,
                Activated boolean,
                Command text
            );
            CREATE TABLE IF NOT EXISTS Log(
                ID text PRIMARY KEY,
                OccuredTime datetime,
                TaskName text NOT NULL,
                Message text,

                FOREIGN KEY (TaskName) REFERENCES Task(Name)
            );
            ''')
            self._conn.commit()
            self._conn.close()

