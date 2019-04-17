class TaskStatus:
    sent = 'sent'
    received = 'received'
    started = 'started'
    succeeded = 'succeeded'
    failed = 'failed'

    @classmethod
    def all(cls):
        return [cls.sent, cls.received, cls.started, cls.succeeded, cls.failed]


class ScheduleCategory:
    wikipedia = 'wikipedia'
    phet = 'phet'

    @classmethod
    def all(cls):
        return [cls.wikipedia, cls.phet]
