class TaskStatus:

    requested = "requested"
    reserved = "reserved"
    started = "started"
    scraper_started = "scraper_started"
    scraper_completed = "scraper_completed"
    scraper_killed = "scraper_killed"
    failed = "failed"
    canceled = "canceled"
    succeeded = "succeeded"

    created_file = "created_file"
    uploaded_file = "uploaded_file"

    @classmethod
    def incomplete(cls):
        return [cls.requested, cls.reserved, cls.started, cls.scraper_started]

    @classmethod
    def all(cls):
        return [
            cls.requested,
            cls.reserved,
            cls.started,
            cls.succeeded,
            cls.scraper_started,
            cls.scraper_completed,
            cls.scraper_killed,
            cls.failed,
            cls.canceled,
        ]

    @classmethod
    def file_events(cls):
        return [cls.created_file, cls.uploaded_file]


class ScheduleCategory:
    gutenberg = "gutenberg"
    other = "other"
    phet = "phet"
    psiram = "psiram"
    stack_exchange = "stack_exchange"
    ted = "ted"
    vikidia = "vikidia"
    wikibooks = "wikibooks"
    wikinews = "wikinews"
    wikipedia = "wikipedia"
    wikiquote = "wikiquote"
    wikisource = "wikisource"
    wikispecies = "wikispecies"
    wikiversity = "wikiversity"
    wikivoyage = "wikivoyage"
    wiktionary = "wiktionary"

    @classmethod
    def all(cls):
        return [
            cls.gutenberg,
            cls.other,
            cls.phet,
            cls.psiram,
            cls.stack_exchange,
            cls.ted,
            cls.vikidia,
            cls.wikibooks,
            cls.wikinews,
            cls.wikipedia,
            cls.wikiquote,
            cls.wikisource,
            cls.wikispecies,
            cls.wikiversity,
            cls.wikivoyage,
            cls.wiktionary,
        ]

    @classmethod
    def get_warehouse_path(cls, category):
        return "/{}".format(category)

    @classmethod
    def all_warehouse_paths(cls):
        return [cls.get_warehouse_path(category) for category in cls.all()]


class ScheduleQueue:
    small = "small"
    medium = "medium"
    large = "large"
    debug = "debug"

    @classmethod
    def all(cls):
        return [cls.small, cls.medium, cls.large, cls.debug]
