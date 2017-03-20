import os, sqlite3


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
            CREATE TABLE IF NOT EXISTS Task(
                Name text PRIMARY KEY,
                Type text,
                Activated boolean,
                Command text
            );
            CREATE TABLE IF NOT EXISTS Log(
                ID text PRIMARY KEY,
                OccurredTime datetime,
                TaskName text NOT NULL,
                Message text,

                FOREIGN KEY (TaskName) REFERENCES Task(Name)
            );
            ''')

    def populate_test_data(self):
        self.add_tasks([
            ('Task1', 'Test', True, 'sleep10'),
            ('Task2', 'Test', True, 'sleep10'),
            ('Task3', 'Test', True, 'sleep10')
        ])

    def get_tasks(self):
        with self.conn:
            self.conn.row_factory = sqlite3.Row
            tasks = []
            for row in self.conn.execute('SELECT Name, Type, Activated, Command FROM Task'):
                tasks.append({
                    'Name': row['Name'],
                    'Type': row['Type'],
                    'Activated': bool(row['Activated']),
                    'Command': row['Command'],
                })
            return tasks

    def add_tasks(self, tasks):
        with self.conn:
            self.conn.executemany('INSERT INTO Task (Name, Type, Activated, Command) values (?, ?, ?, ?)', tasks)