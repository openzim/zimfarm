import os
import sqlite3
from uuid import uuid4

from .status import TaskStatus


class SQLiteDB:
    def __init__(self, path: str = None):
        if path is None:
            self.conn = sqlite3.connect(':memory:')
            self.create_tables()
            self.populate_test_data()
        else:
            self.conn = sqlite3.connect(path)
            if not os.path.exists(path):
                self.create_tables()
                self.populate_test_data()

    def close(self):
        self.conn.close()

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
            (str(uuid4()), 'WikiTask', 'Test', True, 'sleep10'),
            (str(uuid4()), 'Voyage', 'Test', True, 'sleep20'),
            (str(uuid4()), 'Wikimed', 'Test', True, 'sleep40')
        ])

    def get_templates(self, template_ids: [str] = None):
        with self.conn:
            self.conn.row_factory = sqlite3.Row
            sql = 'SELECT ID, Name, Type, Activated, Command FROM Template'
            if template_ids is None or len(template_ids) == 0:
                rows = self.conn.execute(sql)
            else:
                sql += ' WHERE ID IN ({})'.format(','.join(['?'] * len(template_ids)))
                rows = self.conn.execute(sql, tuple(template_ids))
            templates = []
            for row in rows:
                templates.append({
                    'id': row['ID'],
                    'name': row['Name'],
                    'type': row['Type'],
                    'activated': bool(row['Activated']),
                    'command': row['Command'],
                })
            return templates

    def get_template(self, template_id: str):
        templates = self.get_templates([template_id])
        return templates[0] if len(templates) > 0 else None

    def add_templates(self, templates):
        with self.conn:
            self.conn.executemany(
                'INSERT INTO Template (ID, Name, Type, Activated, Command) values (?, ?, ?, ?, ?)', templates)

    def add_task(self, task):
        with self.conn:
            self.conn.execute(
                'INSERT INTO Task (ID, StatusCode, StartTime) values (?, ?, ?)', task)

    def set_task_status(self, task_id: str, status: TaskStatus):
        with self.conn:
            self.conn.execute(
                'UPDATE Task SET StatusCode = ? WHERE ID = ?', (status.value, task_id))

    def get_task(self, task_id: str):
        with self.conn:
            self.conn.row_factory = sqlite3.Row
            row: sqlite3.Row = self.conn.execute(
                'SELECT ID, StatusCode, StartTime, EndTime FROM Task WHERE ID = ?', task_id).fetchone()
            if row is not None:
                return {
                    'id': row['ID'],
                    'status': TaskStatus(row['StatusCode']),
                    'startTime': row['StartTime'],
                    'endTime': row['EndTime']
                }
            else:
                return None
