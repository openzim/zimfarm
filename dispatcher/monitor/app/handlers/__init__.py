from celery.events.state import State


class BaseHandler:
    state: State = None
