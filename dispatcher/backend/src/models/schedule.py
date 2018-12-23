from enum import Enum


class ScheduleCategory(Enum):
    wikipedia = 'wikipedia'
    phet = 'phet'

    @classmethod
    def all(cls) -> ['ScheduleCategory']:
        return [
            cls.wikipedia,
            cls.phet
        ]

    @classmethod
    def all_values(cls) -> [str]:
        return [category.value for category in cls.all()]
