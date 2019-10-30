from bson.objectid import ObjectId, InvalidId


class ScheduleQueryMixin:
    @staticmethod
    def get_schedule_query(schedule_id_or_name: str):
        try:
            schedule_id = ObjectId(schedule_id_or_name)
            return {"_id": schedule_id}
        except InvalidId:
            schedule_name = schedule_id_or_name
            return {"name": schedule_name}
