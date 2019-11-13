import trafaret as t

from common.entities import ScheduleCategory, ScheduleQueue


class ConfigValidator(t.Dict):
    def check(self, config, *args, **kwargs):
        config = super(ConfigValidator, self).check(config, *args, **kwargs)
        flags_validator = get_flags_validator(config.get("task_name"))
        config.update({"flags": flags_validator.check(config.get("flags"))})
        return config


mwoffliner_flags_validator = t.Dict(
    {
        t.Key("mwUrl"): t.URL,
        t.Key("adminEmail"): t.Email,
        t.Key("articleList", optional=True): t.URL,
        t.Key("customZimFavicon", optional=True): t.URL,
        t.Key("customZimTitle", optional=True): t.String,
        t.Key("customZimDescription", optional=True): t.String,
        t.Key("customZimTags", optional=True): t.String,
        t.Key("customMainPage", optional=True): t.String,
        t.Key("filenamePrefix", optional=True): t.String,
        t.Key("format", optional=True): t.List(
            t.Enum(
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
            )
        )
        >> (lambda x: list(set(x))),
        t.Key("keepEmptyParagraphs", optional=True): t.Bool,
        t.Key("mwWikiPath", optional=True): t.String,
        t.Key("mwApiPath", optional=True): t.String,
        t.Key("mwModulePath", optional=True): t.String,
        t.Key("mwDomain", optional=True): t.String,
        t.Key("mwUsername", optional=True): t.String,
        t.Key("mwPassword", optional=True): t.String,
        t.Key("minifyHtml", optional=True): t.Bool,
        t.Key("publisher", optional=True): t.String,
        t.Key("requestTimeout", optional=True): t.Int,
        t.Key("useDownloadCache", optional=True): t.Bool,
        t.Key("skipCacheCleaning", optional=True): t.Bool,
        t.Key("speed", optional=True): t.Float,
        t.Key("verbose", optional=True): t.Bool,
        t.Key("withoutZimFullTextIndex", optional=True): t.Bool,
        t.Key("addNamespaces", optional=True): t.String,
        t.Key("getCategories", optional=True): t.Bool,
        t.Key("noLocalParserFallback", optional=True): t.Bool,
        t.Key("osTmpDir", optional=True): t.String,
    }
)

phet_flags_validator = t.Dict()
gutenberg_flags_validator = t.Dict()
youtube_flags_validator = t.Dict(
    {
        t.Key("type"): t.Enum("channel", "playlist", "user"),
        t.Key("id"): t.String(),
        t.Key("api-key"): t.String(),
        t.Key("format", optional=True): t.Enum("webm", "mp4"),
        t.Key("low-quality", optional=True): t.Bool,
        t.Key("all-subtitles", optional=True): t.Bool,
        t.Key("pagination", optional=True): t.Int,
        t.Key("autoplay", optional=True): t.Bool,
        t.Key("zim-file", optional=True): t.String,
        t.Key("language", optional=True): t.String,
        t.Key("title", optional=True): t.String,
        t.Key("description", optional=True): t.String,
        t.Key("creator", optional=True): t.String,
        t.Key("name", optional=True): t.String,
        t.Key("tags", optional=True): t.String,
        t.Key("profile", optional=True): t.URL,
        t.Key("banner", optional=True): t.URL,
        t.Key("main-color", optional=True): t.String,
        t.Key("secondary-color", optional=True): t.String,
        t.Key("debug", optional=True): t.Bool,
    }
)

resources_validator = t.Dict(
    t.Key("cpu", optional=False, trafaret=t.Int()),
    t.Key("memory", optional=False, trafaret=t.Int()),
    t.Key("disk", optional=False, trafaret=t.Int()),
)

config_validator = ConfigValidator(
    {
        t.Key("task_name"): t.Enum("mwoffliner", "phet", "gutenberg", "youtube"),
        t.Key("queue"): t.Enum(*ScheduleQueue.all()),
        t.Key("warehouse_path"): t.Enum(*ScheduleCategory.all_warehouse_paths()),
        t.Key("image"): t.Dict(
            t.Key(
                "name",
                trafaret=t.Enum(
                    "openzim/mwoffliner",
                    "openzim/phet",
                    "openzim/gutenberg",
                    "openzim/youtube",
                ),
            ),
            t.Key("tag", trafaret=t.String),
        ),
        t.Key("flags"): t.Or(
            mwoffliner_flags_validator,
            phet_flags_validator,
            gutenberg_flags_validator,
            youtube_flags_validator,
        ),
        t.Key("resources", optional=False): resources_validator,
    }
)


def get_flags_validator(task_name):
    if task_name == "phet":
        return phet_flags_validator
    if task_name == "gutenberg":
        return gutenberg_flags_validator
    if task_name == "mwoffliner":
        return mwoffliner_flags_validator
    if task_name == "youtube":
        return youtube_flags_validator
    return t.Dict()


language_validator = t.Dict(
    t.Key("code", optional=False, trafaret=t.String(allow_blank=False)),
    t.Key("name_en", optional=False, trafaret=t.String(allow_blank=False)),
    t.Key("name_native", optional=False, trafaret=t.String(allow_blank=False)),
)

category_validator = t.Enum(*ScheduleCategory.all())


schedule_validator = t.Dict(
    t.Key("name", optional=False, trafaret=t.String(allow_blank=False)),
    t.Key("language", optional=False, trafaret=language_validator),
    t.Key("category", optional=False, trafaret=category_validator),
    t.Key("tags", optional=False, trafaret=t.List(t.String(allow_blank=False))),
    t.Key("enabled", optional=False, trafaret=t.Bool()),
    t.Key("config", optional=False, trafaret=config_validator),
)
