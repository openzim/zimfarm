from routes.base import BaseBlueprint
from .beat import BeatRoute
from .offliner import OfflinerRoute
from .schedule import ScheduleRoute, SchedulesRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.register_route(SchedulesRoute())
        self.register_route(ScheduleRoute())
        self.register_route(BeatRoute())
        self.register_route(OfflinerRoute())
