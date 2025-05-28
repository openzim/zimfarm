# ruff: noqa: N815,S108
from typing import Literal

from pydantic import AnyUrl, EmailStr, Field, SecretStr

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    OptionalField,
    OptionalNotEmptyString,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
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
    articleList: AnyUrl | None = OptionalField(
        title="Article List",
        description="URL to an UTF-8 tsv file containing article names "
        "to include (one per line)",
    )
    articleListToIgnore: AnyUrl | None = OptionalField(
        title="Article List to ignore",
        description="URL to an UTF-8 tsv file containing article names "
        "to ignore (one per line)",
    )
    customMainPage: OptionalNotEmptyString = OptionalField(
        title="Main Page",
        description="Article Name to use as home page. "
        "Automatically built or guessed otherwise.",
    )
    customZimTitle: OptionalZIMTitle = OptionalField(
        title="ZIM Title",
        description="Custom ZIM title. Wiki name otherwise.",
    )
    customZimDescription: OptionalZIMDescription = OptionalField(
        title="ZIM Description",
        description="Max length is 80 chars",
    )
    customZimLongDescription: OptionalZIMLongDescription = OptionalField(
        title="ZIM Long Description",
        description=" Max length is 4000 chars",
    )
    customZimFavicon: AnyUrl | None = OptionalField(
        title="ZIM favicon",
        description="URL to a png to use as favicon. Will be resized to 48x48px.",
    )
    customZimTags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="Semi-colon separated list of ZIM tags",
    )
    customZimLanguage: OptionalNotEmptyString = OptionalField(
        title="ZIM Language metadata",
        description="Custom ISO-639-3 language code for the ZIM",
    )
    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="ZIM publisher metadata. `openZIM` otherwise.",
    )
    filenamePrefix: OptionalNotEmptyString = OptionalField(
        title="Filename prefix",
        description="Custome filename up to the formats and date parts.",
    )
    formats: (
        list[
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
        ]
        | None
    ) = OptionalField(
        description="Which flavours to build, as `<flavour>:<custom-suffix>`. "
        "Empty option is full without suffix.",
        alias="format",
    )

    customFlavour: Literal["/tmp/mwoffliner/extensions/wiktionary_fr.js"] | None = (
        OptionalField(
            title="Custom Flavour",
            description="Custom processor to filter and process articles "
            "(see extensions/*.js)",
        )
    )

    optimisationCacheUrl: OptionalS3OptimizationCache = OptionalField(
        title="Optimisation Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    addNamespaces: OptionalNotEmptyString = OptionalField(
        title="Add Namespaces",
        description="Include addional namespaces (comma separated numbers)",
    )
    getCategories: bool | None = OptionalField(
        title="Add categories",
        description="[WIP] Download category pages",
    )
    keepEmptyParagraphs: bool | None = OptionalField(
        title="Keep empty paragraphs",
        description="Keep all paragraphs, even empty ones.",
    )
    minifyHtml: bool | None = OptionalField(
        title="Minify HTML",
        description="Try to reduce the size of the HTML",
    )

    mwWikiPath: OptionalNotEmptyString = OptionalField(
        title="Wiki Path",
        description="Mediawiki wiki base path. Otherwise `/wiki/`.",
    )
    mwActionApiPath: OptionalNotEmptyString = OptionalField(
        title="API Path",
        description="Mediawiki API path. Otherwise `/w/api.php`.",
    )
    mwRestApiPath: OptionalNotEmptyString = OptionalField(
        title="REST API Path",
        description="Mediawiki REST API path. Otherwise `/w/rest.php`.",
    )
    mwModulePath: OptionalNotEmptyString = OptionalField(
        title="Module Path",
        description="Mediawiki module load path. Otherwise `/w/load.php`.",
    )
    mwDomain: OptionalNotEmptyString = OptionalField(
        title="User Domain",
        description="Mediawiki user domain (for private wikis)",
    )
    mwUsername: OptionalNotEmptyString = OptionalField(
        title="Username",
        description="Mediawiki username (for private wikis)",
    )
    mwPassword: SecretStr | None = OptionalField(
        title="Password",
        description="Mediawiki user password (for private wikis)",
    )

    osTmpDir: OptionalNotEmptyString = OptionalField(
        title="OS Temp Dir",
        description="Override default operating system temporary "
        "directory path environnement variable",
    )
    outputDirectory: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file or build folder. Leave it as `/output`",
    )
    requestTimeout: int | None = OptionalField(
        title="Request Timeout",
        description="Request timeout (in seconds)",
        ge=1,
    )
    speed: float | None = OptionalField(
        title="Speed",
        description="Multiplicator for the number of parallel HTTP requests "
        "on Parsoid backend. Otherwise `1`. Reduce on throttled Wikis.",
    )
    withoutZimFullTextIndex: bool | None = OptionalField(
        description="Don't include a fulltext search index to the ZIM",
    )
    verbose: Literal["info", "log", "warn", "error", "quiet"] | None = OptionalField(
        title="Verbose",
        description="Level of log verbosity, one of info, log, warn, error or "
        "quiet. Default is error.",
    )

    webp: bool | None = OptionalField(
        title="Webp",
        description="Convert images to Webp",
    )

    forceRender: (
        Literal[
            "VisualEditor",
            "WikimediaDesktop",
            "WikimediaMobile",
            "RestApi",
            "ActionParse",
        ]
        | None
    ) = OptionalField(
        title="Force Render",
        description="Force the usage of a specific API end-point/render, "
        "automatically chosen otherwise",
    )

    insecure: bool | None = OptionalField(
        title="Insecure",
        description="Skip HTTPS server authenticity verification step",
    )
