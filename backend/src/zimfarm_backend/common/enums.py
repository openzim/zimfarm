import os
from enum import StrEnum


class TaskStatus(StrEnum):
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
    canceling = "canceling"
    succeeded = "succeeded"

    update = "update"

    created_file = "created_file"
    uploaded_file = "uploaded_file"
    failed_file = "failed_file"
    checked_file = "checked_file"
    check_results_uploaded = "check_results_uploaded"

    @classmethod
    def running(cls):
        return [
            cls.requested,
            cls.reserved,
            cls.started,
            cls.scraper_started,
            cls.scraper_completed,
            cls.scraper_running,
            cls.scraper_killed,
            cls.cancel_requested,
            cls.canceling,
        ]

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
            cls.canceling,
            cls.canceled,
            cls.succeeded,
            cls.failed,
        ]

    @classmethod
    def file_events(cls) -> list[str]:
        return [
            cls.created_file,
            cls.uploaded_file,
            cls.failed_file,
            cls.checked_file,
            cls.check_results_uploaded,
        ]

    @classmethod
    def silent_events(cls) -> list[str]:
        return [*cls.file_events(), cls.scraper_running, cls.update]

    @classmethod
    def all_events(cls) -> list[str]:
        return list(
            filter(
                lambda x: x not in (cls.requested, cls.reserved),
                [*cls.all(), *cls.silent_events()],
            )
        )


class WarehousePath(StrEnum):
    hidden_dev = "/.hidden/dev"
    hidden_endless = "/.hidden/endless"
    hidden_bard = "/.hidden/bard"
    hidden_bsf = "/.hidden/bsf"
    hidden_datacup = "/.hidden/datacup"
    hidden_private = "/.hidden/private"
    hidden_custom_apps = "/.hidden/custom_apps"
    videos = "/videos"
    zimit = "/zimit"
    libretexts = "/libretexts"

    @classmethod
    def all(cls) -> list[str]:
        return [
            *ScheduleCategory.all_warehouse_paths(),
            cls.videos,
            cls.zimit,
            cls.libretexts,
            cls.hidden_dev,
            cls.hidden_private,
            cls.hidden_endless,
            cls.hidden_bard,
            cls.hidden_bsf,
            cls.hidden_datacup,
            cls.hidden_custom_apps,
        ]


class ScheduleCategory(StrEnum):
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
    freecodecamp = "freecodecamp"
    devdocs = "devdocs"
    mindtouch = "mindtouch"

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
            cls.freecodecamp,
            cls.devdocs,
            cls.mindtouch,
        ]

    @classmethod
    def get_warehouse_path(cls, category: str) -> str:
        return f"/{category}"

    @classmethod
    def all_warehouse_paths(cls) -> list[str]:
        custom_paths = {cls.openedx: "mooc"}
        excluded_categories = [cls.wikispecies]
        return [
            cls.get_warehouse_path(custom_paths.get(category, category))
            for category in cls.all()
            if category not in excluded_categories
        ]


class DockerImageName(StrEnum):
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
    freecodecamp = "openzim/freecodecamp"
    devdocs = "openzim/devdocs"
    mindtouch = "openzim/mindtouch"

    @classmethod
    def all(cls) -> set[str]:
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
            cls.freecodecamp,
            cls.devdocs,
            cls.mindtouch,
        }


class SchedulePeriodicity(StrEnum):
    manually = "manually"
    monthly = "monthly"
    quarterly = "quarterly"
    biannualy = "biannualy"
    annually = "annually"

    @classmethod
    def all(cls):
        return [cls.manually, cls.monthly, cls.quarterly, cls.biannualy, cls.annually]


class Platform(StrEnum):
    wikimedia = "wikimedia"
    youtube = "youtube"
    wikihow = "wikihow"
    ifixit = "ifixit"
    ted = "ted"
    devdocs = "devdocs"
    shamela = "shamela"
    libretexts = "libretexts"
    phet = "phet"
    gutenberg = "gutenberg"

    @classmethod
    def all(cls) -> list["Platform"]:
        return [
            cls.wikimedia,
            cls.youtube,
            cls.wikihow,
            cls.ifixit,
            cls.ted,
            cls.devdocs,
            cls.shamela,
            cls.libretexts,
            cls.phet,
            cls.gutenberg,
        ]

    @classmethod
    def get_max_per_worker_tasks_for(cls, platform: str) -> int | None:
        try:
            return int(os.getenv(f"PLATFORM_{platform}_MAX_TASKS_PER_WORKER", ""))
        except (TypeError, ValueError):
            return None

    @classmethod
    def get_max_overall_tasks_for(cls, platform: str) -> int | None:
        try:
            return int(os.getenv(f"PLATFORM_{platform}_MAX_TASKS_TOTAL", ""))
        except (TypeError, ValueError):
            return None
