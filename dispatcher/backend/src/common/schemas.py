from marshmallow import Schema, fields, validates_schema, validate, ValidationError

from common.enum import DockerImageName, Offliner, ScheduleCategory


class ListOfStringEnum(fields.List):
    pass


class StringEnum(fields.String):
    pass


class HexColor(fields.String):
    pass


def validate_positive_integer(value):
    if value < 0:
        raise ValidationError("Can't be negative")


def validate_output(value):
    if value != "/output":
        raise ValidationError("Must be /output.")


validate_category = validate.OneOf(ScheduleCategory.all())
validate_warehouse_path = validate.OneOf(ScheduleCategory.all_warehouse_paths())
validate_offliner = validate.OneOf(Offliner.all())


class SerializableSchema(Schema):

    MAPPING = {
        fields.String: "text",
        StringEnum: "string-enum",
        HexColor: "hex-color",
        fields.Url: "url",
        fields.Email: "email",
        fields.UUID: "text",
        fields.Boolean: "boolean",
        fields.Integer: "integer",
        fields.Float: "float",
        ListOfStringEnum: "list-of-string-enum",
        # fields.List: "list",
        # fields.Date: "date",
        # fields.Time: "text",
        # fields.DateTime: "text",
        # fields.TimeDelta: "text",
    }

    @classmethod
    def field_type_for(cls, field):
        return cls.MAPPING.get(field.__class__, "text")

    @classmethod
    def desc_field(cls, field):
        field_type = cls.field_type_for(field)
        desc = {
            "key": field.name,
            "type": field_type,
            "data_key": field.data_key or field.name,
            "required": field.required,
        }

        if field_type == "list-of-string-enum":
            desc["choices"] = field.inner.validate.choices

        if field_type == "string-enum":
            desc["choices"] = field.validate.choices

        if field.metadata:
            desc.update(field.metadata.get("metadata"))

        return desc

    def to_desc(self):
        return list(map(self.desc_field, self.declared_fields.values()))

    @classmethod
    def ingest(cls, *args, **kwargs):
        return cls().dump(cls().load(*args, **kwargs))


name_schema = fields.String(required=True, validate=validate.Length(min=2))
category_schema = StringEnum(required=True, validate=validate_category)
warehouse_path_schema = StringEnum(required=True, validate=validate_warehouse_path)
offliner_schema = StringEnum(required=True, validate=validate_offliner)


class LanguageSchema(Schema):
    code = fields.String(required=True, validate=validate.Length(min=2, max=3))
    name_en = fields.String(required=True, validate=validate.Length(min=1))
    name_native = fields.String(required=True, validate=validate.Length(min=1))


class ResourcesSchema(Schema):
    cpu = fields.Integer(strict=True, required=True, validate=validate.Range(min=0))
    memory = fields.Integer(strict=True, required=True, validate=validate.Range(min=0))
    disk = fields.Integer(strict=True, required=True, validate=validate.Range(min=0))


class DockerImageSchema(Schema):
    name = fields.String(required=True, validate=validate.OneOf(DockerImageName.all()))
    tag = fields.String(required=True)

    # @validates_schema
    # def validate(self, data, **kwargs):
    #     if data["name"] == DockerImageName.mwoffliner:
    #         allowed_tags = {"1.9.9", "1.9.10", "latest"}
    #     else:
    #         allowed_tags = {"latest"}
    #     if data["tag"] not in allowed_tags:
    #         raise ValidationError(f'tag {data["tag"]} is not an allowed tag')


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
            "description": "Email of the mwoffliner user which will be put in the HTTP user-agent string",
        },
    )

    articleList = fields.URL(
        metadata={
            "label": "Article List",
            "description": "URL to an UTF-8 tsv file containing article names to include (one per line)",
        }
    )
    customMainPage = fields.String(
        metadata={
            "label": "Main Page",
            "description": "Article Name to use as home page. Automatically built or guessed otherwise.",
        }
    )
    customZimTitle = fields.String(
        metadata={
            "label": "ZIM Title",
            "description": "Custom ZIM title. Wiki name otherwise.",
        }
    )
    customZimDescription = fields.String(metadata={"label": "ZIM Description"})
    customZimFavicon = fields.Url(
        metadata={
            "label": "ZIM favicon",
            "description": "URL to a png to use as favicon. Will be resized to 48x48px.",
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
                    ":full",
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
            "description": "Which flavours to build, as `<flavour>:<custom-suffix>`. Empty option is full without suffix.",
        },
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
            "description": "Override default operating system temporary directory path environnement variable",
        }
    )
    outputDirectory = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file or build folder. Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )
    noLocalParserFallback = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Don't fallback to local Parser",
            "description": "Don't fall back to a local MCS or Parsoid, only use remote APIs",
        },
    )
    requestTimeout = fields.Integer(
        metadata={
            "label": "Request Timeout",
            "description": "Request timeout (in seconds)",
        },
        validate=validate.Range(min=1)
    )
    speed = fields.Float(
        metadata={
            "label": "Speed",
            "description": "Multiplicator for the number of parallel HTTP requests on Parsoid backend. Otherwise `1`. Reduce on throttled Wikis.",
        }
    )
    useDownloadCache = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Use Download Cache",
            "description": "Cache all downloaded contents (in between flavours)",
        },
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


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True


class GutenbergFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True


class YoutubeFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    kind = StringEnum(
        metadata={
            "label": "Type",
            "description": "Type of collection. Only `playlist` accepts multiple IDs.",
        },
        validate=validate.OneOf(["channel", "playlist", "user"]),
        data_key="type",
        required=True,
    )
    ident = fields.String(
        metadata={
            "label": "Youtube ID",
            "description": "Youtube ID of the collection. Seperate multiple playlists with commas.",
        },
        data_key="id",
        required=True,
    )
    api_key = fields.String(
        metadata={"label": "API Key", "description": "Youtube API Token"},
        data_key="api-key",
        required=True,
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": "ZIM name",
            "placeholder": "mychannel_eng_all",
        },
        required=True,
    )

    video_format = StringEnum(
        metadata={
            "label": "Video format",
            "description": "Format to download/transcode video to. webm is smaller",
        },
        validate=validate.OneOf(["webm", "mp4"]),
        data_key="format",
    )
    low_quality = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Low Quality",
            "description": "Re-encode video using stronger compression",
        },
        data_key="low-quality",
    )
    concurrency = fields.Integer(
        strict=True,
        metadata={
            "label": "Concurrency",
            "description": "Number of concurrent threads to use",
        },
    )

    all_subtitles = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "All Subtitles",
            "description": "Include auto-generated subtitles",
        },
        data_key="all-subtitles",
    )
    pagination = fields.Integer(
        strict=True,
        metadata={
            "label": "Pagination",
            "description": "Number of videos per page (40 otherwise)",
        },
    )
    autoplay = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Auto-play",
            "description": "Enable autoplay on video articles (home never have autoplay).",
        },
    )
    output = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file or build folder. Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )
    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided)",
        },
        data_key="zim-file",
    )
    language = fields.String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content",
        }
    )
    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your project and ZIM. Default to Channel name (of first video if playlists)",
        }
    )
    description = fields.String(metadata={"label": "Description", "description": ""})
    creator = fields.String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to Channel name or “Youtue Channels”",
        }
    )
    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of Tags for the ZIM file. _videos:yes added automatically",
        }
    )
    profile = fields.Url(
        metadata={
            "label": "Profile Image",
            "description": "Custom profile image. Squared. Will be resized to 100x100px",
        }
    )
    banner = fields.Url(
        metadata={
            "label": "Banner Image",
            "description": "Custom banner image. Will be resized to 1060x175px",
        }
    )
    main_color = HexColor(
        metadata={
            "label": "Main Color",
            "description": "Custom color. Hex/HTML syntax (#DEDEDE). Default to main color of profile image.",
        },
        data_key="main-color",
    )
    secondary_color = HexColor(
        metadata={
            "label": "Secondary Color",
            "description": "Custom secondary color. Hex/HTML syntax (#DEDEDE). Default to secondary color of profile image.",
        },
        data_key="secondary-color",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )


class ScheduleConfigSchema(SerializableSchema):

    task_name = offliner_schema
    warehouse_path = warehouse_path_schema
    image = fields.Nested(DockerImageSchema(), required=True)
    resources = fields.Nested(ResourcesSchema(), required=True)
    flags = fields.Dict(required=True)

    @staticmethod
    def get_offliner_schema(offliner):
        return {
            Offliner.mwoffliner: MWOfflinerFlagsSchema,
            Offliner.youtube: YoutubeFlagsSchema,
            Offliner.gutenberg: GutenbergFlagsSchema,
            Offliner.phet: PhetFlagsSchema,
        }.get(offliner)

    @validates_schema
    def validate(self, data, **kwargs):
        if "task_name" in data and "flag" in data:
            schema = self.get_offliner_schema(data["task_name"])
            data["flags"] = schema.load(data["flags"])


class ScheduleSchema(Schema):
    name = name_schema
    language = fields.Nested(LanguageSchema(), required=True)
    category = category_schema
    tags = fields.List(fields.String(), required=True, default=[])
    enabled = fields.Boolean(required=True, truthy=[True], falsy=[False])
    config = fields.Nested(ScheduleConfigSchema(), required=True)
