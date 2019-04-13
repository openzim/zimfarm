from routes.base import BaseBlueprint
from .beat import BeatRoute
from .schedule import ScheduleRoute, SchedulesRoute, SchedulesBackupRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.register_route(SchedulesRoute())
        self.register_route(ScheduleRoute())
        self.register_route(SchedulesBackupRoute())
        self.register_route(BeatRoute())
