from celery.events.state import State

from .task import BaseTaskEventHandler


class BaseHandler:
    state: State = None
