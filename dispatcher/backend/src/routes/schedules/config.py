from flask import request
from flask.views import MethodView

from errors.http import InvalidRequestJSON
from .. import authenticate
from routes.base import BaseRoute
from .base import ScheduleQueryMixin


class ConfigRoute(MethodView):
    rule = '/<string:schedule>/config/'
    name = 'schedule_config'

    @authenticate
    def patch(self, schedule: str, **kwargs):
        return ''
