from routes import API_PATH
from routes.base import BaseBlueprint

from .schedule import (
    ScheduleCloneRoute,
    ScheduleImageNames,
    ScheduleRoute,
    SchedulesBackupRoute,
    SchedulesRoute,
)


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("schedules", __name__, url_prefix=f"{API_PATH}/schedules")

        self.register_route(SchedulesRoute())
        self.register_route(ScheduleRoute())
        self.register_route(ScheduleImageNames())
        self.register_route(ScheduleCloneRoute())
        self.register_route(SchedulesBackupRoute())
