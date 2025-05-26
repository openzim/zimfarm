# ruff: noqa: N815,S108
from typing import Literal

from pydantic import Field
from pydantic.types import AnyUrl, EmailStr, SecretStr

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMLongDescription,
    ZIMOutputFolder,
    ZIMTitle,
)


class MWOfflinerFlagsSchema(BaseModel):
    mwUrl: AnyUrl = Field(
        title="Wiki URL",
        description="The URL of the mediawiki to scrape",
    )
    adminEmail: EmailStr = Field(
        title="Admin Email",
        description="Email of the mwoffliner user which will be put "
        "in the HTTP user-agent string",
    )
    articleList: AnyUrl = Field(
        title="Article List",
        description="URL to an UTF-8 tsv file containing article names "
        "to include (one per line)",
    )
    articleListToIgnore: AnyUrl = Field(
        title="Article List to ignore",
        description="URL to an UTF-8 tsv file containing article names "
        "to ignore (one per line)",
    )
    customMainPage: NotEmptyString = Field(
        title="Main Page",
        description="Article Name to use as home page. "
        "Automatically built or guessed otherwise.",
    )
    customZimTitle: ZIMTitle | None = Field(
        title="ZIM Title",
        description="Custom ZIM title. Wiki name otherwise.",
        default=None,
    )
    customZimDescription: ZIMDescription = Field(
        title="ZIM Description",
        description="Max length is 80 chars",
    )
    customZimLongDescription: ZIMLongDescription = Field(
        title="ZIM Long Description",
        description=" Max length is 4000 chars",
    )
    customZimFavicon: AnyUrl = Field(
        title="ZIM favicon",
        description="URL to a png to use as favicon. Will be resized to 48x48px.",
    )
    customZimTags: NotEmptyString = Field(
        title="ZIM Tags",
        description="Semi-colon separated list of ZIM tags",
    )
    customZimLanguage: NotEmptyString = Field(
        title="ZIM Language metadata",
        description="Custom ISO-639-3 language code for the ZIM",
    )
    publisher: NotEmptyString = Field(
        title="Publisher",
        description="ZIM publisher metadata. `openZIM` otherwise.",
        default="openZIM",
    )
    filenamePrefix: NotEmptyString = Field(
        title="Filename prefix",
        description="Custome filename up to the formats and date parts.",
    )
    formats: list[
        Literal[
            "nodet,nopic:mini",
            "nodet:mini",
            "nopic:nopic",
            "novid:maxi",
            "",
            "nodet",
            "nopic",
            "novid",
            "nodet,nopic",
        ]
    ] = Field(
        description="Which flavours to build, as `<flavour>:<custom-suffix>`. "
        "Empty option is full without suffix.",
        alias="format",
    )

    customFlavour: Literal["/tmp/mwoffliner/extensions/wiktionary_fr.js"] = Field(
        title="Custom Flavour",
        description="Custom processor to filter and process articles "
        "(see extensions/*.js)",
    )

    optimisationCacheUrl: S3OptimizationCache = Field(
        title="Optimisation Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    addNamespaces: NotEmptyString = Field(
        title="Add Namespaces",
        description="Include addional namespaces (comma separated numbers)",
    )
    getCategories: bool = Field(
        title="Add categories",
        description="[WIP] Download category pages",
    )
    keepEmptyParagraphs: bool = Field(
        title="Keep empty paragraphs",
        description="Keep all paragraphs, even empty ones.",
    )
    minifyHtml: bool = Field(
        title="Minify HTML",
        description="Try to reduce the size of the HTML",
    )

    mwWikiPath: NotEmptyString = Field(
        title="Wiki Path",
        description="Mediawiki wiki base path. Otherwise `/wiki/`.",
        default="/wiki/",
    )
    mwActionApiPath: NotEmptyString = Field(
        title="API Path",
        description="Mediawiki API path. Otherwise `/w/api.php`.",
        default="/w/api.php",
    )
    mwRestApiPath: NotEmptyString = Field(
        title="REST API Path",
        description="Mediawiki REST API path. Otherwise `/w/rest.php`.",
        default="/w/rest.php",
    )
    mwModulePath: NotEmptyString = Field(
        title="Module Path",
        description="Mediawiki module load path. Otherwise `/w/load.php`.",
    )
    mwDomain: NotEmptyString = Field(
        title="User Domain",
        description="Mediawiki user domain (for private wikis)",
    )
    mwUsername: NotEmptyString = Field(
        title="Username",
        description="Mediawiki username (for private wikis)",
    )
    mwPassword: SecretStr = Field(
        title="Password",
        description="Mediawiki user password (for private wikis)",
    )

    osTmpDir: NotEmptyString = Field(
        title="OS Temp Dir",
        description="Override default operating system temporary "
        "directory path environnement variable",
    )
    outputDirectory: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file or build folder. Leave it as `/output`",
        default="/output",
        validate_default=True,
    )
    requestTimeout: int = Field(
        title="Request Timeout",
        description="Request timeout (in seconds)",
        ge=1,
    )
    speed: float = Field(
        title="Speed",
        description="Multiplicator for the number of parallel HTTP requests "
        "on Parsoid backend. Otherwise `1`. Reduce on throttled Wikis.",
        default=1.0,
    )
    withoutZimFullTextIndex: bool = Field(
        description="Don't include a fulltext search index to the ZIM",
    )
    verbose: Literal["info", "log", "warn", "error", "quiet"] = Field(
        title="Verbose",
        description="Level of log verbosity, one of info, log, warn, error or "
        "quiet. Default is error.",
        default="error",
    )

    webp: bool = Field(
        title="Webp",
        description="Convert images to Webp",
    )

    forceRender: Literal[
        "VisualEditor", "WikimediaDesktop", "WikimediaMobile", "RestApi", "ActionParse"
    ] = Field(
        title="Force Render",
        description="Force the usage of a specific API end-point/render, "
        "automatically chosen otherwise",
    )

    insecure: bool = Field(
        title="Insecure",
        description="Skip HTTPS server authenticity verification step",
    )
