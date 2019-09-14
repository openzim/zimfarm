from routes.base import BaseBlueprint
from .config import ConfigRoute
from .schedule import ScheduleRoute, SchedulesRoute, SchedulesBackupRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.register_route(SchedulesRoute())
        self.register_route(ScheduleRoute())
        self.register_route(SchedulesBackupRoute())

        self.add_url_rule(ConfigRoute.rule, view_func=ConfigRoute.as_view(ConfigRoute.name))
