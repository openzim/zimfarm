
from common.languages import all_languages

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
    gutenberg = 'gutenberg'
    other = 'other'
    phet = 'phet'
    psiram = 'psiram'
    stack_exchange = 'stack_exchange'
    ted = 'ted'
    vikidia = 'vikidia'
    wikibooks = 'wikibooks'
    wikinews = 'wikinews'
    wikipedia = 'wikipedia'
    wikiquote = 'wikiquote'
    wikisource = 'wikisource'
    wikispecies = 'wikispecies'
    wikiversity = 'wikiversity'
    wikivoyage = 'wikivoyage'
    wiktionary = 'wiktionary'

    @classmethod
    def all(cls):
        return [cls.gutenberg, cls.other, cls.phet, cls.psiram, cls.stack_exchange,
                cls.ted, cls.vikidia, cls.wikibooks, cls.wikinews, cls.wikipedia,
                cls.wikiquote, cls.wikisource, cls.wikispecies, cls.wikiversity,
                cls.wikivoyage, cls.wiktionary]

    @classmethod
    def get_warehouse_path(cls, category):
        return '/{}'.format(category)

    @classmethod
    def all_warehouse_paths(cls):
        return [cls.get_warehouse_path(category) for category in cls.all()]


class ScheduleQueue:
    small = 'small'
    medium = 'medium'
    large = 'large'
    debug = 'debug'

    @classmethod
    def all(cls):
        return [cls.small, cls.medium, cls.large, cls.debug]


class ScheduleLanguage:

    @classmethod
    def all(cls):
        return [{'code': key,
                 'name_en': value['name_en'], 'name_native': value['name_native']}
                for key, value in all_languages.items()]

    @classmethod
    def get_english_name(cls, lang_code):
        return all_languages.get(lang_code, {}).get("name_en") or lang_code

    @classmethod
    def get_native_name(cls, lang_code):
        return all_languages.get(lang_code, {}).get("name_native") or lang_code
