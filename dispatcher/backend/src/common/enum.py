import os


class TaskStatus:
    requested = "requested"
    reserved = "reserved"
    started = "started"
    scraper_started = "scraper_started"
    scraper_running = "scraper_running"
    scraper_completed = "scraper_completed"
    scraper_killed = "scraper_killed"
    failed = "failed"
    cancel_requested = "cancel_requested"
    canceled = "canceled"
    succeeded = "succeeded"

    update = "update"

    created_file = "created_file"
    uploaded_file = "uploaded_file"
    failed_file = "failed_file"
    checked_file = "checked_file"

    @classmethod
    def incomplete(cls):
        return [
            cls.requested,
            cls.reserved,
            cls.started,
            cls.scraper_started,
            cls.scraper_completed,
        ]

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
        return [cls.created_file, cls.uploaded_file, cls.failed_file, cls.checked_file]

    @classmethod
    def silent_events(cls):
        return cls.file_events() + [cls.scraper_running, cls.update]

    @classmethod
    def all_events(cls):
        return list(
            filter(
                lambda x: x not in (cls.requested, cls.reserved),
                cls.all() + cls.silent_events(),
            )
        )


class WarehousePath:
    hidden_dev = "/.hidden/dev"
    hidden_endless = "/.hidden/endless"
    hidden_bard = "/.hidden/bard"
    hidden_private = "/.hidden/private"
    hidden_custom_apps = "/.hidden/custom_apps"
    videos = "/videos"
    zimit = "/zimit"

    @classmethod
    def all(cls):
        return ScheduleCategory.all_warehouse_paths() + [
            cls.videos,
            cls.zimit,
            cls.hidden_dev,
            cls.hidden_private,
            cls.hidden_endless,
            cls.hidden_bard,
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
    wikihow = "wikihow"
    wikinews = "wikinews"
    wikipedia = "wikipedia"
    wikiquote = "wikiquote"
    wikisource = "wikisource"
    wikispecies = "wikispecies"
    wikiversity = "wikiversity"
    wikivoyage = "wikivoyage"
    wiktionary = "wiktionary"
    ifixit = "ifixit"

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
            cls.wikihow,
            cls.wikinews,
            cls.wikipedia,
            cls.wikiquote,
            cls.wikisource,
            cls.wikispecies,
            cls.wikiversity,
            cls.wikivoyage,
            cls.wiktionary,
            cls.ifixit,
        ]

    @classmethod
    def get_warehouse_path(cls, category):
        return "/{}".format(category)

    @classmethod
    def all_warehouse_paths(cls):
        custom_paths = {cls.openedx: "mooc"}
        excluded_categories = [cls.wikispecies]
        return [
            cls.get_warehouse_path(custom_paths.get(category, category))
            for category in cls.all()
            if category not in excluded_categories
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
    kolibri = "openzim/kolibri"
    wikihow = "openzim/wikihow"
    ifixit = "openzim/ifixit"

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
            cls.kolibri,
            cls.wikihow,
            cls.ifixit,
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
    kolibri = "kolibri"
    wikihow = "wikihow"
    ifixit = "ifixit"

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
            cls.kolibri,
            cls.wikihow,
            cls.ifixit,
        ]

    @classmethod
    def get_image_prefix(cls, offliner):
        prefix = os.getenv(f"DOCKER_REGISTRY_{offliner}", "")
        prefix += "/" if prefix else ""
        return prefix

    @classmethod
    def get_image_name(cls, offliner):
        return (
            cls.get_image_prefix(offliner)
            + {
                cls.mwoffliner: DockerImageName.mwoffliner,
                cls.youtube: DockerImageName.youtube,
                cls.gutenberg: DockerImageName.gutenberg,
                cls.phet: DockerImageName.phet,
                cls.sotoki: DockerImageName.sotoki,
                cls.nautilus: DockerImageName.nautilus,
                cls.ted: DockerImageName.ted,
                cls.openedx: DockerImageName.openedx,
                cls.zimit: DockerImageName.zimit,
                cls.kolibri: DockerImageName.kolibri,
                cls.wikihow: DockerImageName.wikihow,
                cls.ifixit: DockerImageName.ifixit,
            }.get(offliner, "-")
        )


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
    wikihow = "wikihow"

    @classmethod
    def all(cls) -> str:
        return [cls.wikimedia, cls.youtube, cls.wikihow]

    @classmethod
    def get_max_per_worker_tasks_for(cls, platform) -> int:
        try:
            return int(os.getenv(f"PLATFORM_{platform}_MAX_TASKS_PER_WORKER"))
        except (TypeError, ValueError):
            return None

    @classmethod
    def get_max_overall_tasks_for(cls, platform) -> int:
        try:
            return int(os.getenv(f"PLATFORM_{platform}_MAX_TASKS_TOTAL"))
        except (TypeError, ValueError):
            return None
