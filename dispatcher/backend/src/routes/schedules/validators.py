import trafaret as t


mwoffliner_flags_validator = t.Dict({
    t.Key('mwUrl'): t.URL,
    t.Key('adminEmail'): t.Email,
    t.Key('articleList', optional=True): t.URL,
    t.Key('customZimFavicon', optional=True): t.URL,
    t.Key('customZimTitle', optional=True): t.String,
    t.Key('customZimDescription', optional=True): t.String,
    t.Key('customZimTags', optional=True): t.List(t.String),
    t.Key('customMainPage', optional=True): t.String,
    t.Key('filenamePrefix', optional=True): t.String,
    t.Key('format', optional=True): t.List(t.Enum('nodet', 'nopic', 'novid', 'nopdf', 'nodet,nopic', 'nopic,nopdf', 'novid,nopdf')) >> (lambda x: list(set(x))),
    t.Key('keepEmptyParagraphs', optional=True): t.Bool,
    t.Key('mwWikiPath', optional=True): t.String,
    t.Key('mwApiPath', optional=True): t.String,
    t.Key('mwModulePath', optional=True): t.String,
    t.Key('mwDomain', optional=True): t.String,
    t.Key('mwUsername', optional=True): t.String,
    t.Key('mwPassword', optional=True): t.String,
    t.Key('minifyHtml', optional=True): t.Bool,
    t.Key('publisher', optional=True): t.String,
    t.Key('requestTimeout', optional=True): t.Int,
    t.Key('useCache', optional=True): t.Bool,
    t.Key('skipCacheCleaning', optional=True): t.Bool,
    t.Key('speed', optional=True): t.Float,
    t.Key('verbose', optional=True): t.Bool,
    t.Key('withoutZimFullTextIndex', optional=True): t.Bool,
    t.Key('addNamespaces', optional=True): t.String,
    t.Key('getCategories', optional=True): t.Bool,
})


config_validator = t.Dict({
    t.Key('task_name'): t.Enum('offliner.mwoffliner'),
    t.Key('queue'): t.Enum('small', 'medium', 'large', 'debug'),
    t.Key('warehouse_path'): t.Enum(
        '/wikipedia', '/other', '/psiram', '/vikidia', '/wikibooks', '/wikinews',
        '/wikiquote', '/wikisource', '/wikiversity', '/wikivoyage', '/wiktionary'),
    t.Key('image'): t.Dict(
        t.Key('name', trafaret=t.Enum('openzim/mwoffliner')),
        t.Key('tag', trafaret=t.String)),
    t.Key('flags'): mwoffliner_flags_validator
})
