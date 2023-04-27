from marshmallow import fields, validate

from common.schemas import ListOfStringEnum, LongString, SerializableSchema, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_longdescription,
)


class MWOfflinerFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    mwUrl = fields.URL(
        required=True,
        metadata={
            "label": "Wiki URL",
            "description": "The URL of the mediawiki to scrape",
        },
    )
    adminEmail = fields.Email(
        required=True,
        metadata={
            "label": "Admin Email",
            "description": "Email of the mwoffliner user which will be put "
            "in the HTTP user-agent string",
        },
    )

    articleList = fields.URL(
        metadata={
            "label": "Article List",
            "description": "URL to an UTF-8 tsv file containing article names "
            "to include (one per line)",
        }
    )
    articleListToIgnore = fields.URL(
        metadata={
            "label": "Article List to ignore",
            "description": "URL to an UTF-8 tsv file containing article names "
            "to ignore (one per line)",
        }
    )
    customMainPage = fields.String(
        metadata={
            "label": "Main Page",
            "description": "Article Name to use as home page. "
            "Automatically built or guessed otherwise.",
        }
    )
    customZimTitle = fields.String(
        metadata={
            "label": "ZIM Title",
            "description": "Custom ZIM title. Wiki name otherwise.",
        }
    )
    customZimDescription = fields.String(
        metadata={"label": "ZIM Description", "description": "Max length is 80 chars"},
        validate=validate_zim_description,
    )
    customZimLongDescription = LongString(
        metadata={
            "label": "ZIM Long Description",
            "description": " Max length is 4000 chars",
        },
        validate=validate_zim_longdescription,
    )
    customZimFavicon = fields.Url(
        metadata={
            "label": "ZIM favicon",
            "description": "URL to a png to use as favicon. "
            "Will be resized to 48x48px.",
        }
    )
    customZimTags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "Semi-colon separated list of ZIM tags",
        }
    )
    publisher = fields.String(
        metadata={
            "label": "Publisher",
            "description": "ZIM publisher metadata. `Kiwix` otherwise.",
        }
    )
    filenamePrefix = fields.String(
        metadata={
            "label": "Filename prefix",
            "description": "Custome filename up to the formats and date parts.",
        }
    )
    formats = ListOfStringEnum(
        fields.String(
            validate=validate.OneOf(
                [
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
            )
        ),
        data_key="format",
        metadata={
            "label": "Flavours",
            "description": "Which flavours to build, as `<flavour>:<custom-suffix>`. "
            "Empty option is full without suffix.",
        },
    )
    customFlavour = StringEnum(
        metadata={
            "label": "Custom Flavour",
            "description": "Custom processor to filter and process articles "
            "(see extensions/*.js)",
        },
        validate=validate.OneOf(
            ["/tmp/mwoffliner/extensions/wiktionary_fr.js"]  # nosec
        ),
    )

    optimisationCacheUrl = fields.Url(
        metadata={
            "label": "Optimisation Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        }
    )

    addNamespaces = fields.String(
        metadata={
            "label": "Add Namespaces",
            "description": "Include addional namespaces (comma separated numbers)",
        }
    )
    getCategories = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Add categories",
            "description": "[WIP] Download category pages",
        },
    )
    keepEmptyParagraphs = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Keep empty paragraphs",
            "description": "Keep all paragraphs, even empty ones.",
        },
    )
    minifyHtml = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Minify HTML",
            "description": "Try to reduce the size of the HTML",
        },
    )

    mwWikiPath = fields.String(
        metadata={
            "label": "Wiki Path",
            "description": "Mediawiki wiki base path. Otherwise `/wiki/`.",
        }
    )
    mwApiPath = fields.String(
        metadata={
            "label": "API Path",
            "description": "Mediawiki API path. Otherwise `/w/api.php`.",
        }
    )
    mwModulePath = fields.String(
        metadata={
            "label": "Module Path",
            "description": "Mediawiki module load path. Otherwise `/w/load.php`.",
        }
    )
    mwDomain = fields.String(
        metadata={
            "label": "User Domain",
            "description": "Mediawiki user domain (for private wikis)",
        }
    )
    mwUsername = fields.String(
        metadata={
            "label": "Username",
            "description": "Mediawiki username (for private wikis)",
        }
    )
    mwPassword = fields.String(
        metadata={
            "label": "Password",
            "description": "Mediawiki user password (for private wikis)",
        }
    )

    osTmpDir = fields.String(
        metadata={
            "label": "OS Temp Dir",
            "description": "Override default operating system temporary "
            "directory path environnement variable",
        }
    )
    outputDirectory = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file or build folder. "
            "Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )
    requestTimeout = fields.Integer(
        metadata={
            "label": "Request Timeout",
            "description": "Request timeout (in seconds)",
        },
        validate=validate.Range(min=1),
    )
    speed = fields.Float(
        metadata={
            "label": "Speed",
            "description": "Multiplicator for the number of parallel HTTP requests "
            "on Parsoid backend. Otherwise `1`. Reduce on throttled Wikis.",
        }
    )
    withoutZimFullTextIndex = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Without Full Text Index",
            "description": "Don't include a fulltext search index to the ZIM",
        },
    )
    verbose = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Verbose",
            "description": "Print debug information to the stdout",
        },
    )

    webp = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Webp",
            "description": "Convert images to Webp",
        },
    )
