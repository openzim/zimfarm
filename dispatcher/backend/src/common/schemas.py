from marshmallow import Schema, fields, validates_schema, validate, ValidationError, post_load

from common.entities import DockerImage, ScheduleConfig
from common.enum import DockerImageName, ScheduleQueue


class DockerImageSchema(Schema):
    name = fields.String(required=True, validate=validate.OneOf(DockerImageName.all()))
    tag = fields.String(required=True)

    @validates_schema
    def validate(self, data, **kwargs):
        if data['name'] == DockerImageName.mwoffliner:
            allowed_tags = {'1.9.9', '1.9.10', 'latest'}
        else:
            allowed_tags = {'latest'}
        if data['tag'] not in allowed_tags:
            raise ValidationError(f'tag {data["tag"]} is not an allowed tag')

    @post_load
    def make_docker_image(self, data, **kwargs):
        return DockerImage(**data)


class MWOfflinerConfigFlagsSchema(Schema):
    # mwoffliner required fields
    mwUrl = fields.URL(required=True)
    adminEmail = fields.Email(required=True)

    # mwoffliner optional fields
    articleList = fields.URL()
    filenamePrefix = fields.String()
    publisher = fields.String()
    format = fields.List(fields.String(validate=validate.OneOf([
        ':full',
        'nodet,nopic:mini',
        'nodet:mini',
        'nopic:nopic',
        'novid:maxi',
        '',
        'nodet',
        'nopic',
        'novid',
        'nodet,nopic'
    ])))

    # mwoffliner booleans
    keepEmptyParagraphs = fields.Bool()
    minifyHtml = fields.Bool()
    useCache = fields.Bool()
    skipCacheCleaning = fields.Bool()
    verbose = fields.Bool()
    withoutZimFullTextIndex = fields.Bool()
    getCategories = fields.Bool()
    noLocalParserFallback = fields.Bool()
    
    # customization
    customZimFavicon = fields.String()
    customZimTitle = fields.String()
    customZimDescription = fields.String()
    customZimTags = fields.List(fields.String())
    customMainPage = fields.String()
    
    # connectivity
    mwWikiPath = fields.String()
    mwApiPath = fields.String()
    mwModulePath = fields.String()
    mwDomain = fields.String()
    mwUsername = fields.String()
    mwPassword = fields.String()


class ScheduleConfigSchema(Schema):
    image = fields.Nested(DockerImageSchema(), required=True)
    flags = fields.Dict(required=True)
    queue = fields.String(required=True, validate=validate.OneOf(ScheduleQueue.all()))
    task_name = fields.String(required=True)
    warehouse_path = fields.String(required=True)

    @validates_schema
    def validate(self, data, **kwargs):
        image: DockerImage = data['image']
        if image.name == DockerImageName.mwoffliner:
            schema = MWOfflinerConfigFlagsSchema()
        else:
            schema = Schema.from_dict({})
        data['flags'] = schema.load(data['flags'])

    @post_load
    def make_schedule_config(self, data, **kwargs):
        return ScheduleConfig(**data)
