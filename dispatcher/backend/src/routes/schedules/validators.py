from trafaret import Dict, Key, String, URL, Email


class CrontabValidator(Dict):
    def __init__(self):
        super().__init__(
            Key('minute', default='*', trafaret=String(allow_blank=False)),
            Key('hour', default='*', trafaret=String(allow_blank=False)),
            Key('day_of_week', default='*', trafaret=String(allow_blank=False)),
            Key('day_of_month', default='*', trafaret=String(allow_blank=False)),
            Key('month_of_year', default='*', trafaret=String(allow_blank=False)))


class MWOfflinerConfigValidator(Dict):
    def __init__(self):
        super().__init__(
            Key('mwUrl', trafaret=URL()),
            Key('adminEmail', trafaret=Email())
        )