from trafaret import Dict, Key, String


class CrontabValidator(Dict):
    def __init__(self):
        super().__init__(
            Key('minute', default='*', trafaret=String(allow_blank=False)),
            Key('hour', default='*', trafaret=String(allow_blank=False)),
            Key('day_of_week', default='*', trafaret=String(allow_blank=False)),
            Key('day_of_month', default='*', trafaret=String(allow_blank=False)),
            Key('month_of_year', default='*', trafaret=String(allow_blank=False))
        )