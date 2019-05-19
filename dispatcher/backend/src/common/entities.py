class TaskStatus:
    sent = 'sent'
    received = 'received'
    started = 'started'
    succeeded = 'succeeded'
    container_started = 'container_started'
    container_finished = 'container_finished'
    failed = 'failed'
    retried = 'retried'
    revoked = 'revoked'

    @classmethod
    def all(cls):
        return [cls.sent, cls.received, cls.started, cls.succeeded, cls.failed, cls.retried, cls.revoked]


class ScheduleCategory:
    wikipedia = 'wikipedia'
    phet = 'phet'

    @classmethod
    def all(cls):
        return [cls.wikipedia, cls.phet]
