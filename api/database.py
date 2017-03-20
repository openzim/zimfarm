import sqlite3
from uuid import uuid4


class SQLiteDB:
    def __init__(self, path: str = None):
        if path is None:
            self.conn = sqlite3.connect(':memory:')
        else:
            self.conn = sqlite3.connect(path)
        self.create_tables()
        self.populate_test_data()

    def create_tables(self):
        with self.conn:
            self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS Template (
                ID text PRIMARY KEY,
                Name text,
                Type text,
                Activated boolean,
                Command text
            );
            CREATE TABLE IF NOT EXISTS Task (
                ID text PRIMARY KEY,
                StatusCode integer,
                StartTime datetime,
                EndTime datetime
            );
            CREATE TABLE IF NOT EXISTS Log (
                TaskID text PRIMARY KEY,
                StdInput text,
                StdOutput text,

                FOREIGN KEY (TaskID) REFERENCES Task(ID)
            );
            ''')

    def populate_test_data(self):
        self.add_templates([
            (uuid4(), 'WikiTask', 'Test', True, 'sleep10'),
            (uuid4(), 'Voyage', 'Test', True, 'sleep20'),
            (uuid4(), 'Wikimed', 'Test', True, 'sleep40')
        ])

    def get_templates(self):
        with self.conn:
            self.conn.row_factory = sqlite3.Row
            tasks = []
            for row in self.conn.execute('SELECT, ID, Name, Type, Activated, Command FROM Template'):
                tasks.append({
                    'id': row['ID'],
                    'name': row['Name'],
                    'type': row['Type'],
                    'activated': bool(row['Activated']),
                    'command': row['Command'],
                })
            return tasks

    def add_templates(self, templates):
        with self.conn:
            self.conn.executemany(
                'INSERT INTO Template (ID, Name, Type, Activated, Command) values (?, ?, ?, ?, ?)', templates)
