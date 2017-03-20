import sqlite3


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
                Name text PRIMARY KEY,
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
            ('WikiTask', 'Test', True, 'sleep10'),
            ('Voyage', 'Test', True, 'sleep20'),
            ('Wikimed', 'Test', True, 'sleep40')
        ])

    def get_templates(self):
        with self.conn:
            self.conn.row_factory = sqlite3.Row
            tasks = []
            for row in self.conn.execute('SELECT Name, Type, Activated, Command FROM Template'):
                tasks.append({
                    'Name': row['Name'],
                    'Type': row['Type'],
                    'Activated': bool(row['Activated']),
                    'Command': row['Command'],
                })
            return tasks

    def add_templates(self, templates):
        with self.conn:
            self.conn.executemany(
                'INSERT INTO Template (Name, Type, Activated, Command) values (?, ?, ?, ?)', templates)

db = SQLiteDB()