# ruff: noqa: E501
import base64
import datetime
from collections.abc import Callable, Generator
from ipaddress import IPv4Address
from typing import Any, cast

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from faker import Faker
from faker.providers import DynamicProvider
from pydantic import BaseModel
from pytest import FixtureRequest, Mark
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import Platform, TaskStatus, WarehousePath
from zimfarm_backend.common.roles import ROLES, RoleEnum
from zimfarm_backend.common.schemas.models import (
    DockerImageSchema,
    LanguageSchema,
    ResourcesSchema,
    ScheduleConfigSchema,
)
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
)
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import (
    Base,
    OfflinerDefinition,
    RequestedTask,
    Schedule,
    ScheduleDuration,
    ScheduleHistory,
    Sshkey,
    Task,
    User,
    Worker,
)
from zimfarm_backend.db.offliner import create_offliner
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema
from zimfarm_backend.db.schedule import DEFAULT_SCHEDULE_DURATION, get_schedule_or_none
from zimfarm_backend.utils.offliners import expanded_config
from zimfarm_backend.utils.timestamp import get_timestamp_for_status
from zimfarm_backend.utils.token import (
    generate_access_token,
    get_public_key_fingerprint,
    sign_message_with_rsa_key,
)


@pytest.fixture
def dbsession() -> Generator[OrmSession]:
    session = Session()
    # Ensure we are starting with an empty database
    engine = session.get_bind()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def data_gen(faker: Faker) -> Faker:
    """Sets up faker to generate random data for testing.

    Registers task_status as a provider.
    data_gen.task_status() returns a task status.
    All other providers from Faker can be used accordingly.
    """
    task_status_provider = DynamicProvider(
        provider_name="task_status",
        elements=list(TaskStatus),
    )
    faker.add_provider(task_status_provider)

    # Setting a fixed seed ensures that Faker generates the same fake data
    # on every test run. This makes tests deterministic and reproducible,
    # so failures are easier to debug and tests are more reliable.
    # Other test submodules can choose a new seed value.
    faker.seed_instance(123)

    return faker


@pytest.fixture
def rsa_private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def rsa_public_key(rsa_private_key: RSAPrivateKey) -> RSAPublicKey:
    return rsa_private_key.public_key()


@pytest.fixture
def rsa_public_key_data(rsa_private_key: RSAPrivateKey) -> bytes:
    """Serialize public key using PEM format."""
    return rsa_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )


@pytest.fixture
def auth_message(user: User) -> str:
    return f"{user.username}:{getnow().isoformat()}"


@pytest.fixture
def rsa_x_sshauth_signature(rsa_private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(auth_message, encoding="ascii")
    )
    return base64.b64encode(signature).decode()


@pytest.fixture
def access_token(user: User) -> str:
    return generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )


@pytest.fixture
def mwoffliner_flags() -> OfflinerSpecSchema:
    return OfflinerSpecSchema.model_validate_json(
        r"""
{
  "stdOutput": "outputDirectory",
  "stdStats": false,
  "flags": {
    "mwUrl": {
      "type": "url",
      "required": true,
      "title": "Wiki URL",
      "description": "The URL of the mediawiki to scrape"
    },
    "adminEmail": {
      "type": "email",
      "required": true,
      "title": "Admin Email",
      "description": "Email of the mwoffliner user which will be put in the HTTP user-agent string"
    },
    "articleList": {
      "type": "string",
      "required": false,
      "title": "Article List",
      "description": "List of articles to include. Comma separated list of titles or HTTP(S) URL to a file with one title (in UTF8) per line"
    },
    "articleListToIgnore": {
      "type": "string",
      "required": false,
      "title": "Article List to ignore",
      "description": "List of articles to ignore. Comma separated list of titles or HTTP(S) URL to a file with one title (in UTF8) per line"
    },
    "customMainPage": {
      "type": "string",
      "required": false,
      "title": "Main Page",
      "description": "Article Name to use as home page. Automatically built or guessed otherwise."
    },
    "customZimTitle": {
      "type": "string",
      "required": false,
      "title": "ZIM Title",
      "description": "Custom ZIM title. Wiki name otherwise.",
      "minLength": 1,
      "maxLength": 30
    },
    "customZimDescription": {
      "type": "string",
      "required": false,
      "title": "ZIM Description",
      "description": "Max length is 80 chars",
      "minLength": 1,
      "maxLength": 80
    },
    "customZimLongDescription": {
      "type": "string",
      "required": false,
      "title": "ZIM Long Description",
      "description": "Max length is 4000 chars",
      "minLength": 1,
      "maxLength": 4000
    },
    "customZimFavicon": {
      "type": "url",
      "required": false,
      "title": "ZIM favicon",
      "description": "URL to a png to use as favicon. Will be resized to 48x48px."
    },
    "customZimTags": {
      "type": "string",
      "required": false,
      "title": "ZIM Tags",
      "description": "Semi-colon separated list of ZIM tags"
    },
    "customZimLanguage": {
      "type": "string",
      "required": false,
      "title": "ZIM Language Metadata",
      "description": "Custom ISO-639-3 language code for the ZIM",
      "pattern": "^[a-z]{3}(,[a-z]{3})*$"
    },
    "publisher": {
      "type": "string",
      "required": false,
      "title": "Publisher",
      "isPublisher": true,
      "description": "ZIM publisher metadata. `openZIM` otherwise."
    },
    "filenamePrefix": {
      "type": "string",
      "required": false,
      "title": "Filename prefix",
      "description": "Custome filename up to the formats and date parts."
    },
    "formats": {
      "type": "list-of-string-enum",
      "required": false,
      "title": "Formats",
      "description": "Which flavours to build, as `<flavour>:<custom-suffix>`. Empty option is full without suffix.",
      "alias": "format",
      "choices": [
        { "title": "NODET_NOPIC_MINI", "value": "nodet,nopic:mini" },
        { "title": "NODET_MINI", "value": "nodet:mini" },
        { "title": "NOPIC_NOPIC", "value": "nopic:nopic" },
        { "title": "NOVID_MAXI", "value": "novid:maxi" },
        { "title": "EMPTY", "value": "" },
        { "title": "NODET", "value": "nodet" },
        { "title": "NOPIC", "value": "nopic" },
        { "title": "NOVID", "value": "novid" },
        { "title": "NODET_NOPIC", "value": "nodet,nopic" }
      ]
    },
    "customFlavour": {
      "type": "string-enum",
      "required": false,
      "title": "Custom Flavour",
      "description": "Custom processor to filter and process articles (see extensions/*.js)",
      "choices": [
        {
          "title": "WIKTIONARY_FR",
          "value": "/tmp/mwoffliner/extensions/wiktionary_fr.js"
        }
      ]
    },
    "optimisationCacheUrl": {
      "type": "url",
      "required": false,
      "title": "Optimisation Cache URL",
      "description": "S3 Storage URL including credentials and bucket",
      "secret": true
    },
    "addNamespaces": {
      "type": "string",
      "required": false,
      "title": "Add Namespaces",
      "description": "Include addional namespaces (comma separated numbers)"
    },
    "getCategories": {
      "type": "boolean",
      "required": false,
      "title": "Add categories",
      "description": "[WIP] Download category pages"
    },
    "keepEmptyParagraphs": {
      "type": "boolean",
      "required": false,
      "title": "Keep empty paragraphs",
      "description": "Keep all paragraphs, even empty ones."
    },
    "minifyHtml": {
      "type": "boolean",
      "required": false,
      "title": "Minify HTML",
      "description": "Try to reduce the size of the HTML"
    },
    "mwWikiPath": {
      "type": "string",
      "required": false,
      "title": "Wiki Path",
      "description": "Mediawiki wiki base path. Otherwise `/wiki/`."
    },
    "mwActionApiPath": {
      "type": "string",
      "required": false,
      "title": "API Path",
      "description": "Mediawiki API path. Otherwise `/w/api.php`."
    },
    "mwRestApiPath": {
      "type": "string",
      "required": false,
      "title": "REST API Path",
      "description": "Mediawiki REST API path. Otherwise `/w/rest.php`."
    },
    "mwModulePath": {
      "type": "string",
      "required": false,
      "title": "Module Path",
      "description": "Mediawiki module load path. Otherwise `/w/load.php`."
    },
    "mwIndexPhpPath": {
      "type": "string",
      "required": false,
      "title": "index.php Path",
      "description": "Path to Mediawiki index.php. Otherwise `/w/index.php`."
    },
    "mwDomain": {
      "type": "string",
      "required": false,
      "title": "User Domain",
      "description": "Mediawiki user domain (for private wikis)"
    },
    "mwUsername": {
      "type": "string",
      "required": false,
      "title": "Username",
      "description": "Mediawiki username (for private wikis)"
    },
    "mwPassword": {
      "type": "string",
      "required": false,
      "title": "Password",
      "description": "Mediawiki user password (for private wikis)",
      "secret": true
    },
    "osTmpDir": {
      "type": "string",
      "required": false,
      "title": "OS Temp Dir",
      "description": "Override default operating system temporary directory path environnement variable"
    },
    "outputDirectory": {
      "type": "string",
      "required": false,
      "title": "Output folder",
      "description": "Output folder for ZIM file or build folder. Leave it as `/output`",
      "pattern": "^/output$"
    },
    "requestTimeout": {
      "type": "integer",
      "required": false,
      "title": "Request Timeout",
      "description": "Request timeout (in seconds)",
      "min": 1
    },
    "speed": {
      "type": "float",
      "title": "Speed",
      "required": false,
      "description": "Multiplicator for the number of parallel HTTP requests on Parsoid backend. Otherwise `1`. Reduce on throttled Wikis."
    },
    "withoutZimFullTextIndex": {
      "type": "boolean",
      "title": "Without ZIM Full Text Index",
      "required": false,
      "description": "Don't include a fulltext search index to the ZIM"
    },
    "verbose": {
      "type": "string-enum",
      "required": false,
      "title": "Verbose",
      "description": "Level of log verbosity, one of info, log, warn, error or quiet. Default is error.",
      "choices": [
        { "title": "INFO", "value": "info" },
        { "title": "LOG", "value": "log" },
        { "title": "WARN", "value": "warn" },
        { "title": "ERROR", "value": "error" },
        { "title": "QUIET", "value": "quiet" }
      ]
    },
    "webp": {
      "type": "boolean",
      "title": "Webp",
      "description": "Convert images to Webp",
      "required": false
    },
    "forceRender": {
      "type": "string-enum",
      "required": false,
      "title": "Force Render",
      "description": "Force the usage of a specific API end-point/render, automatically chosen otherwise",
      "choices": [
        { "title": "VISUAL_EDITOR", "value": "VisualEditor" },
        { "title": "WIKIMEDIA_DESKTOP", "value": "WikimediaDeskto" },
        { "title": "WIKIMEDIA_MOBILE", "value": "WikimediaMobile" },
        { "title": "REST_API", "value": "RestApi" },
        { "title": "ACTION_PARSE", "value": "ActionParse" }
      ]
    },
    "insecure": {
      "type": "boolean",
      "title": "Insecure",
      "description": "Skip HTTPS server authenticity verification step",
      "required": false
    },
    "langVariant": {
      "type": "string",
      "title": "Language Variant",
      "description": "Use a specific language variant, only for wikis supporting language conversion",
      "required": false
    }
  }
}
"""
    )


@pytest.fixture
def mwoffliner(dbsession: OrmSession) -> OfflinerSchema:
    return create_offliner(
        dbsession,
        offliner_id="mwoffliner",
        base_model="DashModel",
        docker_image_name="openzim/mwoffliner",
        command_name="mwoffliner",
    )


@pytest.fixture
def mwoffliner_definition(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
) -> OfflinerDefinitionSchema:
    """Create an mwoffliner definition in the database."""
    definition = OfflinerDefinition(
        offliner="mwoffliner",
        version="initial",
        schema=mwoffliner_flags.model_dump(mode="json"),
        created_at=getnow(),
    )
    dbsession.add(definition)
    dbsession.flush()
    return create_offliner_definition_schema(definition)


@pytest.fixture
def mwoffliner_schema_cls(
    mwoffliner_flags: OfflinerSpecSchema, mwoffliner: OfflinerSchema
):
    return build_offliner_model(mwoffliner, mwoffliner_flags)


@pytest.fixture
def ted_flags() -> OfflinerSpecSchema:
    return OfflinerSpecSchema.model_validate_json(
        r"""
{
  "stdOutput": true,
  "stdStats": false,
  "flags": {
    "topics": {
      "type": "string",
      "required": false,
      "title": "Topics",
      "description": "Comma-separated list of topics to scrape; as given on ted.com/talks. Pass all for all topics. Exclusive with playlists and links, only one must be set."
    },
    "playlists": {
      "type": "string",
      "required": false,
      "title": "TED Playlists",
      "description": "Comma-separated list of TED playlist IDs to scrape. Pass all for all playlists. Exclusive with topics and links, only one must set."
    },
    "links": {
      "type": "string",
      "required": false,
      "title": "Links",
      "description": "Comma-separated TED talk URLs to scrape, each in the format: https://www.ted.com/talks/<talk_slug>. Exclusive with topics and playlists, only one must set.",
      "customValidator": "validate_ted_links"
    },
    "languages": {
      "type": "string",
      "required": false,
      "title": "Languages",
      "description": "Comma-separated list of ISO-639-3 language codes to filter videos. Do not pass this parameter for all languages",
      "pattern": "^[a-z]{3}(,[a-z]{3})*$",
      "customValidator": "language_code"
    },
    "subtitles_enough": {
      "type": "boolean",
      "required": false,
      "title": "Subtitles enough?",
      "description": "Whether to include videos that have a subtitle in requested language(s) if audio is in another language"
    },
    "subtitles": {
      "type": "string",
      "required": false,
      "title": "Subtitles Setting",
      "description": "Language setting for subtitles. all: include all available subtitles, matching (default): only subtitles matching language(s), none: include no subtitle. Also accepts comma-separated list of language(s)"
    },
    "video_format": {
      "type": "string-enum",
      "required": false,
      "title": "Video format",
      "description": "Format to download/transcode video to. webm is smaller",
      "choices": [
        { "title": "WEBM", "value": "webm" },
        { "title": "MP4", "value": "mp4" }
      ]
    },
    "low_quality": {
      "type": "boolean",
      "required": false,
      "title": "Low Quality",
      "description": "Re-encode video using stronger compression"
    },
    "autoplay": {
      "type": "boolean",
      "required": false,
      "title": "Autoplay videos",
      "description": "Enable autoplay on videos. Behavior differs on platforms/browsers"
    },
    "name": {
      "type": "string",
      "required": true,
      "title": "Name",
      "description": "ZIM name. Used as identifier and filename (date will be appended)",
      "pattern": "^([a-z0-9\\-\\.]+_)([a-z\\-]+_)([a-z0-9\\-\\.]+)$"
    },
    "title": {
      "type": "string",
      "required": false,
      "title": "Title",
      "description": "Custom title for your ZIM. Based on selection otherwise",
      "minLength": 1,
      "maxLength": 30
    },
    "description": {
      "type": "string",
      "required": false,
      "title": "Description",
      "description": "Custom description for your ZIM. Based on selection otherwise",
      "minLength": 1,
      "maxLength": 80
    },
    "long_description": {
      "type": "string",
      "required": false,
      "title": "Long description",
      "description": "Custom long description for your ZIM. Based on selection otherwise",
      "minLength": 1,
      "maxLength": 4000
    },
    "creator": {
      "type": "string",
      "required": false,
      "title": "Content Creator",
      "description": "Name of content creator. Defaults to TED"
    },
    "publisher": {
      "type": "string",
      "required": false,
      "title": "Publisher",
      "isPublisher": true,
      "description": "Custom publisher name (ZIM metadata). \"openZIM\" otherwise"
    },
    "tags": {
      "type": "string",
      "required": false,
      "title": "ZIM Tags",
      "description": "List of comma-separated Tags for the ZIM file. category:ted, ted, and _videos:yes added automatically"
    },
    "optimization_cache": {
      "type": "url",
      "required": false,
      "title": "Optimization Cache URL",
      "description": "URL with credentials and bucket name to S3 Optimization Cache",
      "secret": true
    },
    "use_any_optimized_version": {
      "type": "boolean",
      "required": false,
      "title": "Use any optimized version",
      "description": "Use the cached files if present, whatever the version"
    },
    "output": {
      "type": "string",
      "required": false,
      "title": "Output folder",
      "description": "Output folder for ZIM file(s). Leave it as `/output`",
      "pattern": "^/output$"
    },
    "tmp_dir": {
      "type": "string",
      "required": false,
      "title": "Temp folder",
      "description": "Where to create temporay build folder. Leave it as `/output`",
      "pattern": "^/output$"
    },
    "zim_file": {
      "type": "string",
      "required": false,
      "title": "ZIM filename",
      "description": "ZIM file name (based on ZIM name if not provided)",
      "pattern": "^([a-z0-9\\-\\.]+_)([a-z\\-]+_)([a-z0-9\\-\\.]+_)([a-z0-9\\-\\.]+_|)([\\d]{4}-[\\d]{2}|\\{period\\}).zim$"
    },
    "debug": {
      "type": "boolean",
      "required": false,
      "title": "Debug",
      "description": "Enable verbose output"
    },
    "threads": {
      "type": "integer",
      "required": false,
      "title": "Threads",
      "description": "Number of parallel threads to use while downloading"
    },
    "locale": {
      "type": "string",
      "required": false,
      "title": "Locale",
      "description": "The locale to use for the translations in ZIM"
    },
    "language_threshold": {
      "type": "integer",
      "required": false,
      "title": "Language Threshold",
      "description": "Add language in ZIM metadata only if present in at least this percentage of videos. Number between 0 and 1. Defaults to 0.5: language must be used in 50% of videos to be considered as ZIM language.",
      "min": 0,
      "max": 1
    }
  },
  "modelValidators": [
    {
      "name": "check_exclusive_fields",
      "fields": ["links", "topics", "playlists"]
    }
  ]
}
"""
    )


@pytest.fixture
def ted_offliner(dbsession: OrmSession) -> OfflinerSchema:
    return create_offliner(
        dbsession,
        offliner_id="ted",
        base_model="DashModel",
        docker_image_name="openzim/ted",
        command_name="ted2zim",
    )


@pytest.fixture
def ted_flags_schema_cls(ted_flags: OfflinerSpecSchema, ted_offliner: OfflinerSchema):
    return build_offliner_model(ted_offliner, ted_flags)


@pytest.fixture
def tedoffliner_definition(
    dbsession: OrmSession, ted_flags: OfflinerSchema
) -> OfflinerDefinitionSchema:
    """Create an offliner definition in the database."""
    definition = OfflinerDefinition(
        offliner="ted",
        version="initial",
        schema=ted_flags.model_dump(mode="json"),
        created_at=getnow(),
    )
    dbsession.add(definition)
    dbsession.flush()
    return create_offliner_definition_schema(definition)


@pytest.fixture
def create_user(
    dbsession: OrmSession,
    rsa_public_key: RSAPublicKey,
    rsa_public_key_data: bytes,
    data_gen: Faker,
) -> Callable[..., User]:
    def _create_user(*, permission: RoleEnum = RoleEnum.ADMIN):
        pubkey_pkcs8 = rsa_public_key_data.decode("ascii")

        user = User(
            username=data_gen.first_name(),
            password_hash=generate_password_hash("testpassword"),
            email=data_gen.safe_email(),
            scope=ROLES[permission],
        )
        dbsession.add(user)

        key = Sshkey(
            name=data_gen.word(),
            key=rsa_public_key_data.decode("ascii") + " test@localhost",
            fingerprint=get_public_key_fingerprint(rsa_public_key),
            type="RSA",
            added=getnow(),
            pkcs8_key=pubkey_pkcs8,
        )
        key.user = user

        dbsession.add(key)
        dbsession.flush()

        return user

    return _create_user


@pytest.fixture
def users(
    create_user: Callable[..., User],
    request: FixtureRequest,
) -> list[User]:
    """Adds users to the database using the num_users mark."""
    mark = cast(
        Mark,
        request.node.get_closest_marker(  # pyright: ignore[reportUnknownMemberType]
            "num_users"
        ),
    )
    if mark and len(mark.args) > 0:
        num_users = int(mark.args[0])
    else:
        num_users = 10

    if mark:
        permission = mark.kwargs.get("permission", RoleEnum.ADMIN)
    else:
        permission = RoleEnum.ADMIN

    users: list[User] = []

    for _ in range(num_users):
        user = create_user(permission=permission)
        users.append(user)

    return users


@pytest.fixture
def user(create_user: Callable[..., User]):
    return create_user()


@pytest.fixture
def create_worker(dbsession: OrmSession, user: User) -> Callable[..., Worker]:
    _user = user

    def _create_worker(
        *,
        name: str = "testworker",
        cpu: int = 2,
        memory: int = 1024,
        disk: int = 1024,
        offliners: list[str] | None = None,
        platforms: dict[str, int] | None = None,
        contexts: list[str] | None = None,
        last_seen: datetime.datetime | None = None,
        last_ip: IPv4Address | None = None,
        user: User | None = None,
        deleted: bool = False,
    ) -> Worker:
        user = _user if user is None else user

        _platforms = platforms or {
            Platform.wikimedia: 100,
            Platform.youtube: 100,
        }

        _ip = last_ip or IPv4Address("127.0.0.1")

        worker = Worker(
            name=name,
            selfish=False,
            cpu=cpu,
            memory=memory,
            disk=disk,
            offliners=offliners or ["mwoffliner", "youtube"],
            platforms=_platforms,
            contexts=contexts or [],
            last_seen=last_seen or getnow(),
            last_ip=_ip,
            deleted=deleted,
        )
        worker.user_id = user.id
        dbsession.add(worker)
        dbsession.flush()
        return worker

    return _create_worker


@pytest.fixture
def worker(create_worker: Callable[..., Worker]) -> Worker:
    """Create a worker for testing"""
    return create_worker()


@pytest.fixture
def schedule_duration(
    dbsession: OrmSession, schedule: Schedule, worker: Worker
) -> ScheduleDuration:
    """Create a schedule duration for testing"""
    duration = ScheduleDuration(
        default=True,
        value=3600,  # 1 hour
        on=getnow(),
    )
    duration.schedule = schedule
    duration.worker = worker
    dbsession.add(duration)
    dbsession.flush()
    return duration


@pytest.fixture
def language() -> LanguageSchema:
    return LanguageSchema(code="eng", name="English")


@pytest.fixture
def create_schedule_config(
    mwoffliner_schema_cls: type[BaseModel],
    mwoffliner: OfflinerSchema,
) -> Callable[..., ScheduleConfigSchema]:
    def _create_schedule_config(
        cpu: int = 2, memory: int = 2**30, disk: int = 2**30
    ) -> ScheduleConfigSchema:
        return ScheduleConfigSchema(
            warehouse_path=WarehousePath.videos,
            image=DockerImageSchema(
                name=mwoffliner.docker_image_name,
                tag="latest",
            ),
            resources=ResourcesSchema(
                cpu=cpu,
                memory=memory,
                disk=disk,
            ),
            offliner=mwoffliner_schema_cls.model_validate(
                {
                    "offliner_id": mwoffliner.id,
                    "mwUrl": "https://en.wikipedia.org",
                    "adminEmail": "test@kiwix.org",
                    "mwPassword": "test-password",
                }
            ),
            platform=Platform.wikimedia,
            monitor=True,
        )

    return _create_schedule_config


@pytest.fixture
def schedule_config(
    create_schedule_config: Callable[..., ScheduleConfigSchema],
) -> ScheduleConfigSchema:
    return create_schedule_config(cpu=1, memory=2**30, disk=2**30)


@pytest.fixture
def create_schedule(
    dbsession: OrmSession,
    schedule_config: ScheduleConfigSchema,
    language: LanguageSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    _language = language
    _schedule_config = schedule_config

    def _create_schedule(
        *,
        name: str = "testschedule",
        category: str = "wikipedia",
        periodicity: str = "monthly",
        notification: dict[str, Any] | None = None,
        language: LanguageSchema | None = None,
        tags: list[str] | None = None,
        context: str | None = None,
        schedule_config: ScheduleConfigSchema | None = None,
        worker: Worker | None = None,
    ) -> Schedule:
        language = _language if language is None else language
        schedule_config = (
            _schedule_config if schedule_config is None else schedule_config
        )
        schedule = Schedule(
            name=name,
            tags=tags or ["nopic"],
            category=category,
            config=schedule_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            enabled=True,
            language_code=language.code,
            periodicity=periodicity,
            notification=notification,
            context=context or "",
        )
        schedule.offliner_definition_id = mwoffliner_definition.id

        schedule_duration = ScheduleDuration(
            value=DEFAULT_SCHEDULE_DURATION.value,
            on=DEFAULT_SCHEDULE_DURATION.on,
            default=True,
        )
        schedule_duration.worker = worker
        schedule.durations.append(schedule_duration)

        history_entry = ScheduleHistory(
            author="test",
            created_at=getnow(),
            comment=None,
            config=schedule.config,
            name=schedule.name,
            category=schedule.category,
            enabled=schedule.enabled,
            language_code=schedule.language_code,
            tags=schedule.tags,
            periodicity=schedule.periodicity,
            context=schedule.context,
        )
        schedule.history_entries.append(history_entry)

        dbsession.add(schedule)
        dbsession.flush()
        return schedule

    return _create_schedule


@pytest.fixture
def schedule(create_schedule: Callable[..., Schedule]):
    return create_schedule()


@pytest.fixture(scope="module")
def create_event():
    def _create_event(code: str, timestamp: datetime.datetime, **kwargs: Any):
        event = {"code": code, "timestamp": timestamp}
        event.update(kwargs)
        return event

    return _create_event


@pytest.fixture
def create_requested_task(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    worker: Worker,
    create_event: Callable[..., Any],
    schedule_config: ScheduleConfigSchema,
    mwoffliner: OfflinerSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    _schedule_config = schedule_config
    _worker = worker

    def _create_requested_task(
        *,
        schedule_name: str = "testschedule",
        status: TaskStatus = TaskStatus.requested,
        requested_by: str = "testuser",
        priority: int = 0,
        worker: Worker | None = None,
        request_date: datetime.datetime | None = None,
        schedule_config: ScheduleConfigSchema | None = None,
    ):
        now = getnow()
        events = list(TaskStatus)

        timestamp = [(event.value, request_date or now) for event in events]
        events = [
            create_event(event.value, get_timestamp_for_status(timestamp, event.value))
            for event in events
        ]

        schedule_config = (
            _schedule_config if schedule_config is None else schedule_config
        )

        schedule = get_schedule_or_none(dbsession, schedule_name=schedule_name)
        if schedule is None:
            schedule = create_schedule(
                name=schedule_name, schedule_config=schedule_config
            )

        requested_task = RequestedTask(
            status=status,
            timestamp=timestamp,
            updated_at=request_date or now,
            events=events,
            requested_by=requested_by,
            priority=priority,
            config=expanded_config(
                schedule_config, mwoffliner, mwoffliner_definition
            ).model_dump(mode="json", context={"show_secrets": True}),
            upload={},
            notification={},
            original_schedule_name=schedule_name,
            context=schedule.context,
        )
        requested_task.schedule = schedule
        requested_task.offliner_definition_id = schedule.offliner_definition_id
        requested_task.worker = _worker if worker is None else worker
        dbsession.add(requested_task)
        dbsession.flush()
        return requested_task

    return _create_requested_task


@pytest.fixture
def requested_task(
    create_requested_task: Callable[..., RequestedTask],
    schedule_config: ScheduleConfigSchema,
):
    return create_requested_task(schedule_config=schedule_config)


@pytest.fixture
def requested_tasks(
    create_requested_task: Callable[..., RequestedTask],
    request: FixtureRequest,
    data_gen: Faker,
) -> list[RequestedTask]:
    """Adds requested tasks to the database using the num_requested_tasks mark."""
    mark = cast(
        Mark,
        request.node.get_closest_marker(  # pyright: ignore[reportUnknownMemberType]
            "num_requested_tasks"
        ),
    )
    if mark and len(mark.args) > 0:
        num_requested_tasks = int(mark.args[0])
    else:
        num_requested_tasks = 10

    tasks: list[RequestedTask] = []
    for _ in range(num_requested_tasks):
        tasks.append(create_requested_task(status=data_gen.task_status()))
    return tasks


@pytest.fixture
def create_task(
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    dbsession: OrmSession,
) -> Callable[..., Task]:
    _worker = worker

    def _create_task(
        *,
        schedule_name: str = "testschedule",
        status: TaskStatus = TaskStatus.requested,
        worker: Worker | None = None,
        requested_task: RequestedTask | None = None,
    ) -> Task:
        if requested_task is None:
            requested_task = create_requested_task(
                schedule_name=schedule_name, status=status
            )
        task = Task(
            updated_at=requested_task.updated_at,
            events=requested_task.events,
            debug={},
            status=requested_task.status,
            timestamp=requested_task.timestamp,
            requested_by=requested_task.requested_by,
            canceled_by=None,
            container={},
            priority=requested_task.priority,
            config=requested_task.config,
            notification=requested_task.notification,
            files={},
            upload=requested_task.upload,
            original_schedule_name=requested_task.original_schedule_name,
            context=requested_task.context,
        )
        task.id = requested_task.id
        task.offliner_definition_id = requested_task.offliner_definition_id
        task.schedule_id = requested_task.schedule_id
        task.worker_id = _worker.id if worker is None else worker.id
        dbsession.add(task)
        dbsession.delete(requested_task)
        dbsession.flush()
        return task

    return _create_task


@pytest.fixture
def task(create_task: Callable[..., Task]) -> Task:
    return create_task()
