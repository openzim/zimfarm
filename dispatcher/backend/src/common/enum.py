import os


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
    failed_file = "failed_file"

    @classmethod
    def incomplete(cls):
        return [cls.requested, cls.reserved, cls.started, cls.scraper_started]

    @classmethod
    def complete(cls):
        return [cls.failed, cls.canceled, cls.succeeded]

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
        return [cls.created_file, cls.uploaded_file, cls.failed_file]

    @classmethod
    def all_events(cls):
        return list(
            filter(
                lambda x: x not in (cls.requested, cls.reserved),
                cls.all() + cls.file_events(),
            )
        )


class WarehousePath:
    hidden_dev = "/.hidden/dev"
    hidden_endless = "/.hidden/endless"
    hidden_custom_apps = "/.hidden/custom_apps"
    videos = "/videos"

    @classmethod
    def all(cls):
        return ScheduleCategory.all_warehouse_paths() + [
            cls.videos,
            cls.hidden_dev,
            cls.hidden_endless,
            cls.hidden_custom_apps,
        ]


class ScheduleCategory:
    gutenberg = "gutenberg"
    other = "other"
    phet = "phet"
    psiram = "psiram"
    stack_exchange = "stack_exchange"
    ted = "ted"
    openedx = "openedx"
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
            cls.openedx,
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
        custom_paths = {cls.openedx: "mooc"}
        return [
            cls.get_warehouse_path(custom_paths.get(category, category))
            for category in cls.all()
        ]


class DockerImageName:
    mwoffliner = "openzim/mwoffliner"
    youtube = "openzim/youtube"
    gutenberg = "openzim/gutenberg"
    phet = "openzim/phet"
    sotoki = "openzim/sotoki"
    nautilus = "openzim/nautilus"
    ted = "openzim/ted"
    openedx = "openzim/openedx"
    zimit = "openzim/zimit"

    @classmethod
    def all(cls) -> set:
        return {
            cls.mwoffliner,
            cls.youtube,
            cls.gutenberg,
            cls.phet,
            cls.sotoki,
            cls.nautilus,
            cls.ted,
            cls.openedx,
            cls.zimit,
        }


class Offliner:
    mwoffliner = "mwoffliner"
    youtube = "youtube"
    gutenberg = "gutenberg"
    phet = "phet"
    sotoki = "sotoki"
    nautilus = "nautilus"
    ted = "ted"
    openedx = "openedx"
    zimit = "zimit"

    @classmethod
    def all(cls):
        return [
            cls.mwoffliner,
            cls.youtube,
            cls.gutenberg,
            cls.phet,
            cls.sotoki,
            cls.nautilus,
            cls.ted,
            cls.openedx,
            cls.zimit,
        ]


class SchedulePeriodicity:
    manually = "manually"
    monthly = "monthly"
    quarterly = "quarterly"
    biannualy = "biannualy"
    annually = "annually"

    @classmethod
    def all(cls):
        return [cls.manually, cls.monthly, cls.quarterly, cls.biannualy, cls.annually]


class Platform:
    wikimedia = "wikimedia"
    youtube = "youtube"

    @classmethod
    def all(cls) -> str:
        return [cls.wikimedia, cls.youtube]

    @classmethod
    def get_max_concurrent_for(cls, platform) -> int:
        try:
            return int(os.getenv(f"PLATFORM_{platform}_MAX_TASKS"))
        except (TypeError, ValueError):
            return None
