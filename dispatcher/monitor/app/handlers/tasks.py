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
    def get_task_id_from_event(event: dict) -> Optional[ObjectId]:
        try:
            return ObjectId(event.get('uuid'))
        except InvalidId:
            return None

    @staticmethod
    def get_timestamp(task: Task) -> datetime:
        return datetime.fromtimestamp(task.timestamp, tz=pytz.utc)

    @staticmethod
    def get_timestamp_from_event(event: dict) -> datetime:
        return datetime.fromtimestamp(event['timestamp'], tz=pytz.utc)

    def save_event(self, task_id: ObjectId, code: str, timestamp: datetime, **kwargs):
        # insert event and sort by timestamp
        event = {'code': code, 'timestamp': timestamp}
        update = {'$push': {'events': {'$each': [event], '$sort': {'timestamp': 1}}}}
        Tasks().update_one({'_id': task_id}, update)

        # update task status, timestamp and other fields
        task_updates = {f'timestamp.{code}': timestamp}
        if 'container' not in code:
            task_updates['status'] = code
        if 'hostname' in kwargs:
            task_updates['hostname'] = kwargs['hostname']
        if 'files' in kwargs:
            task_updates['files'] = kwargs['files']
        if 'command' in kwargs:
            task_updates['container.command'] = kwargs['command']
        if 'image' in kwargs:
            task_updates['container.image'] = kwargs['image']
        if 'exit_code' in kwargs:
            task_updates['container.exit_code'] = kwargs['exit_code']
        if 'stdout' in kwargs:
            task_updates['container.stdout'] = kwargs['stdout']
        if 'stderr' in kwargs:
            task_updates['container.stderr'] = kwargs['stderr']
        if 'log' in kwargs:
            task_updates['container.log'] = kwargs['log']
        if 'task_name' in kwargs:
            task_updates['debug.task_name'] = kwargs['task_name']
        if 'task_args' in kwargs:
            task_updates['debug.task_args'] = kwargs['task_args']
        if 'task_kwargs' in kwargs:
            task_updates['debug.task_kwargs'] = kwargs['task_kwargs']
        if 'exception' in kwargs:
            task_updates['debug.exception'] = kwargs['exception']
        if 'traceback' in kwargs:
            task_updates['debug.traceback'] = kwargs['traceback']
        if 'timeout' in kwargs:
            task_updates['container.timeout'] = kwargs['timeout']
        Tasks().update_one({'_id': task_id}, {'$set': task_updates})

        self._update_schedule_most_recent_task_status(task_id)

    @staticmethod
    def _update_schedule_most_recent_task_status(task_id):
        # get schedule and last event
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

        # update schedule most recent task
        schedule_id = task['schedule']['_id']
        last_event_code = task['last_event']['code']
        last_event_timestamp = task['last_event']['timestamp']
        if 'container' in last_event_code:
            return
        schedule_updates = {'most_recent_task': {
            '_id': task_id, 'status': last_event_code, 'updated_at': last_event_timestamp}}
        Schedules().update_one({'_id': schedule_id}, {'$set': schedule_updates})


class TaskSentEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Sent: {task_id}')

        kwargs = {'task_name': task.name,
                  'task_args': ast.literal_eval(task.args),
                  'task_kwargs': ast.literal_eval(task.kwargs)}
        self.save_event(task_id, TaskEvent.sent, self.get_timestamp(task), **kwargs)


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


class TaskRevokedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        terminated = event.get('terminated')
        signum = event.get('signum')

        logger.info(f'Task Revoked: {task_id}, terminated: {terminated}, signum: {signum}')

        self.save_event(task_id, TaskEvent.revoked, self.get_timestamp(task))


class TaskContainerStartedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task_id = self.get_task_id_from_event(event)
        timestamp = self.get_timestamp_from_event(event)

        image = event.get('image')
        command = event.get('command')

        logger.info(f'Task Container Started: {task_id}, {command}')

        self.save_event(task_id, TaskEvent.container_started, timestamp, image=image, command=command)


class TaskContainerFinishedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task_id = self.get_task_id_from_event(event)
        timestamp = self.get_timestamp_from_event(event)

        exit_code = event.get('exit_code')
        stdout = event.get('stdout')
        stderr = event.get('stderr')
        log = event.get('log')

        logger.info(f'Task Container Finished: {task_id}, {exit_code}')

        self.save_event(task_id, TaskEvent.container_finished, timestamp,
                        exit_code=exit_code, stdout=stdout, stderr=stderr, log=log)


class TaskContainerKilledEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task_id = self.get_task_id_from_event(event)
        timestamp = self.get_timestamp_from_event(event)

        timeout = event.get('timeout')

        logger.info(f'Task Container Killed: {task_id}, after {timeout}s')

        self.save_event(task_id, TaskEvent.container_killed, timestamp, timeout=timeout)
