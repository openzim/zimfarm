from bson import ObjectId

from common.entities import ScheduleConfig, DockerImage
from common.mongo import Schedules
from common.schemas import ScheduleConfigSchema
from errors.http import ScheduleNotFound


class ScheduleService:
    @staticmethod
    def get_config(schedule_id: ObjectId) -> ScheduleConfig:
        schedule = Schedules().find_one({'_id': schedule_id}, {'config': 1})
        if not schedule:
            raise ScheduleNotFound()

        config = ScheduleConfigSchema().load(schedule['config'])
        config['image'] = DockerImage(**config['image'])
        return ScheduleConfig(**config)


    @staticmethod
    def update_config(image: dict):
        pass