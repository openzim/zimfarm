from trafaret import Dict, Key, String, URL, Email, Bool, Float


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
            Key('adminEmail', trafaret=Email()),
            Key('deflateTmpHtml', optional=True, trafaret=Bool()),
            Key('keepHtml', optional=True, trafaret=Bool()),
            Key('language', optional=True, trafaret=String()),
            Key('languageInverter', optional=True, trafaret=String()),
            Key('languageTrigger', optional=True, trafaret=String()),
            Key('parsoidUrl', optional=True, trafaret=URL()),
            Key('project', optional=True, trafaret=String()),
            Key('projectInverter', optional=True, trafaret=String()),
            Key('resume', optional=True, trafaret=Bool()),
            Key('speed', optional=True, trafaret=Float()),
            Key('verbose', optional=True, trafaret=Bool()),
            Key('skipHtmlCache', optional=True, trafaret=Bool()),
            Key('withZimFullTextIndex', optional=True, trafaret=Bool()),
            Key('mobileLayout', optional=True, trafaret=Bool()),
        )