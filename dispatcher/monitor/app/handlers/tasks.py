import ast
import logging
from datetime import datetime
from typing import Optional

import pytz
from bson.objectid import ObjectId, InvalidId
from celery.events.state import Task

from entities import TaskEvent
from handlers import BaseHandler
from mongo import Tasks, Schedules

logger = logging.getLogger(__name__)


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event) -> Task:
        self.state.event(event)
        task: Task = self.state.tasks.get(event['uuid'])
        return task

    @staticmethod
    def get_task_id(task: Task) -> Optional[ObjectId]:
        try:
            return ObjectId(task.uuid)
        except InvalidId:
            return None

    @staticmethod
    def get_timestamp(task: Task) -> datetime:
        return datetime.fromtimestamp(task.timestamp, tz=pytz.utc)

    @staticmethod
    def save_event(task_id: ObjectId, code: str, timestamp: datetime, **kwargs):
        # insert event
        event = {'code': code, 'timestamp': timestamp}
        update = {'$push': {'events': {'$each': [event], '$sort': {'timestamp': 1}}}}
        Tasks().update_one({'_id': task_id}, update)

        # get last event
        cursor = Tasks().aggregate([
            {'$match': {'_id': task_id}},
            {'$project': {
                'schedule._id': 1,
                'last_event': {'$arrayElemAt': ['$events', -1]}
            }}
        ])
        tasks = [task for task in cursor]
        task = tasks[0] if tasks else None
        if not task:
            return
        last_event = task['last_event']

        # update task status, timestamp and other fields
        code = last_event['code']
        timestamp = last_event['timestamp']
        task_updates = {'status': code, f'timestamp.{code}': timestamp}
        if 'hostname' in kwargs:
            task_updates['hostname'] = kwargs['hostname']
        if 'command' in kwargs:
            task_updates['command'] = kwargs['command']
        if 'files' in kwargs:
            task_updates['files'] = kwargs['files']
        if 'exception' in kwargs:
            task_updates['error.exception'] = kwargs['exception']
        if 'traceback' in kwargs:
            task_updates['error.traceback'] = kwargs['traceback']
        if 'exit_code' in kwargs:
            task_updates['error.exit_code'] = kwargs['exit_code']
        if 'stderr' in kwargs:
            task_updates['error.stderr'] = kwargs['stderr']
        Tasks().update_one({'_id': task_id}, {'$set': task_updates})

        # update schedule most recent task
        schedule_id = task['schedule']['_id']
        schedule_updates = {'most_recent_task': {'_id': task_id, 'status': code, 'updated_at': timestamp}}
        Schedules().update_one({'_id': schedule_id}, {'$set': schedule_updates})


class TaskSentEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Sent: {task_id}')

        self.save_event(task_id, TaskEvent.sent, self.get_timestamp(task))


class TaskReceivedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Received: {task_id}')

        self.save_event(task_id, TaskEvent.received, self.get_timestamp(task))


class TaskStartedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Started: {task_id}, hostname={task.worker.hostname}')

        self.save_event(task_id, TaskEvent.started, self.get_timestamp(task), hostname=task.worker.hostname)


class TaskSucceededEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)
        files = ast.literal_eval(task.result)

        logger.info(f'Task Succeeded: {task_id}, {task.timestamp}, {task.runtime}')

        self.save_event(task_id, TaskEvent.succeeded, self.get_timestamp(task),
                        hostname=task.worker.hostname, files=files)


class TaskFailedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Failed: {task_id}, {task.timestamp}')

        self.save_event(task_id, TaskEvent.failed, self.get_timestamp(task), hostname=task.worker.hostname,
                        exception=task.exception, traceback=task.traceback)


class TaskRetriedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Retried: {task_id}, {task.timestamp}')

        self.save_event(task_id, TaskEvent.retried, self.get_timestamp(task), hostname=task.worker.hostname,
                        exception=task.exception, traceback=task.traceback)


class TaskContainerErrorEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task_id = ObjectId(event.get('uuid'))

        exit_code = event.get('exit_code')
        command = event.get('command')
        stderr = event.get('stderr')
        timestamp = datetime.fromtimestamp(event['timestamp'], tz=pytz.utc)

        logger.info(f'Task Container Error: {task_id}, {exit_code}, {command}')

        self.save_event(task_id, TaskEvent.container_error, timestamp, exit_code=exit_code,
                        command=command, stderr=stderr)
