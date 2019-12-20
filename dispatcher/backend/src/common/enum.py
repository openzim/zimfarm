class TaskStatus:
    requested = "requested"
    reserved = "reserved"
    started = "started"
    scraper_started = "scraper_started"
    scraper_completed = "scraper_completed"
    scraper_killed = "scraper_killed"
    failed = "failed"
    cancel_requested = "cancel_requested"
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
            cls.scraper_started,
            cls.scraper_completed,
            cls.scraper_killed,
            cls.cancel_requested,
            cls.canceled,
            cls.succeeded,
            cls.failed,
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


class DockerImageName:
    mwoffliner = "openzim/mwoffliner"
    youtube = "openzim/youtube"
    gutenberg = "openzim/gutenberg"
    phet = "openzim/phet"

    @classmethod
    def all(cls) -> set:
        return {cls.mwoffliner, cls.phet, cls.gutenberg}


class Offliner:
    mwoffliner = "mwoffliner"
    youtube = "youtube"
    gutenberg = "gutenberg"
    phet = "phet"

    @classmethod
    def all(cls):
        return [cls.mwoffliner, cls.youtube, cls.gutenberg, cls.phet]
