import pytest
from marshmallow import ValidationError

from common.enum import DockerImageName, ScheduleQueue
from common.schemas import DockerImageSchema, MWOfflinerConfigFlagsSchema, ScheduleConfigSchema


class TestDockerImageSchema:
    @pytest.mark.parametrize('data', [
        {},  # empty
        {'tag': 'latest'},  # missing name
        {'name': DockerImageName.mwoffliner},  # missing tag
        {'name': DockerImageName.mwoffliner, 'tag': 'latest', 'field': 'abc'},  # extra field
        {'name': 'ubuntu', 'tag': 'alpine'},  # bad name and tag
    ])
    def test_bad_data(self, data):
        with pytest.raises(ValidationError):
            DockerImageSchema().load(data)

    @pytest.mark.parametrize('name', DockerImageName.all())
    @pytest.mark.parametrize('tag', ['', 'abc', 123, None])
    def test_tag_failing(self, name, tag):
        """Test when name is valid, tag value is bad, result in validation to fail"""
        with pytest.raises(ValidationError):
            DockerImageSchema().load({'name': name, 'tag': tag})

    @pytest.mark.parametrize('name, tag', [
        (DockerImageName.mwoffliner, '1.9.9'),
        (DockerImageName.mwoffliner, '1.9.10'),
        (DockerImageName.mwoffliner, 'latest'),
        (DockerImageName.phet, 'latest'),
        (DockerImageName.gutenberg, 'latest'),
    ])
    def test_passing(self, name, tag):
        DockerImageSchema().load({'name': name, 'tag': tag})


class TestMWOfflinerConfigFlagSchema:
    required_fields = ['mwUrl', 'adminEmail']
    bool_fields = [
        'keepEmptyParagraphs', 'minifyHtml', 'useCache', 'skipCacheCleaning',
        'verbose', 'withoutZimFullTextIndex', 'getCategories', 'noLocalParserFallback',
    ]
    string_fields = [
        'filenamePrefix', 'publisher', 'customZimFavicon', 'customZimTitle', 'customZimDescription',
        'customZimTags', 'customMainPage', 'mwWikiPath', 'mwApiPath', 'mwModulePath', 'mwDomain',
        'mwUsername', 'mwPassword'
    ]

    def _make_flag(self, **kwargs):
        if 'mwUrl' not in kwargs:
            kwargs['mwUrl'] = 'http://en.wikipedia.org/'
        if 'adminEmail' not in kwargs:
            kwargs['adminEmail'] = 'contact@kiwix.org'
        return kwargs

    @pytest.mark.parametrize('data', [
        {},  # empty
        {'adminEmail': 'contact@kiwix.org'},  # missing mwUrl
        {'mwUrl': 'http://en.wikipedia.org/'},  # missing adminEmail
        {
            'mwUrl': 'http://example.org/',
            'adminEmail': 'contact@kiwix.org',
            'field': 'abc'
        },  # extra field,
        {'mwUrl': 'not_url', 'adminEmail': 'contact@kiwix.org'},  # bad mwUrl
        {'mwUrl': 'http://en.wikipedia.org/', 'adminEmail': 'not_email'},  # bad adminEmail
    ])
    def test_bad_data(self, data):
        with pytest.raises(ValidationError):
            MWOfflinerConfigFlagsSchema().load(data)

    def test_required_passing(self):
        flag = {'mwUrl': 'https://en.wikipedia.org/', 'adminEmail': 'contact@kiwix.org'}
        MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('value', [
        [],
        [''],
        [':full'],
        [':full', 'nodet,nopic:mini']
    ])
    def test_format_passing(self, value):
        flag = self._make_flag(**{'format': value})
        MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('value', [None, 123, '123', True, {}, ['not_valid'], [123]])
    def test_format_failing(self, value):
        flag = self._make_flag(**{'format': value})
        with pytest.raises(ValidationError):
            MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('field', bool_fields)
    @pytest.mark.parametrize('value', [True, False])
    def test_boolean_field_passing(self, field, value):
        flag = self._make_flag(**{field: value})
        MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('field', bool_fields)
    @pytest.mark.parametrize('value', [None, 123, '123', [], {}])
    def test_boolean_field_failing(self, field, value):
        flag = self._make_flag(**{field: value})
        with pytest.raises(ValidationError):
            MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('field', string_fields)
    def test_string_field_passing(self, field):
        if field == 'customZimTags':
            flag = self._make_flag(**{field: ['test_string']})
        else:
            flag = self._make_flag(**{field: 'test_string'})
        MWOfflinerConfigFlagsSchema().load(flag)

    @pytest.mark.parametrize('field', string_fields)
    @pytest.mark.parametrize('value', [None, 123, True, [], {}])
    def test_string_field_failing(self, field, value):
        if field == 'customZimTags':
            flag = self._make_flag(**{field: [value]})
        else:
            flag = self._make_flag(**{field: value})
        with pytest.raises(ValidationError):
            MWOfflinerConfigFlagsSchema().load(flag)


class TestScheduleConfigSchema:
    def _make_config(self, **kwargs):
        if 'image' not in kwargs and 'flags' not in kwargs:
            kwargs.update({
                'image': {
                    'name': DockerImageName.mwoffliner,
                    'tag': 'latest',
                },
                'flags': {
                    'mwUrl': 'https://en.wikipedia.org/',
                    'adminEmail': 'contact@kiwix.org',
                }
            })
        if 'queue' not in kwargs:
            kwargs['queue'] = ScheduleQueue.large
        if 'task_name' not in kwargs:
            kwargs['task_name'] = 'offliner.mwoffliner'
        if 'warehouse_path' not in kwargs:
            kwargs['warehouse_path'] = '/wikipedia'
        return kwargs

    def test_extra_field(self):
        with pytest.raises(ValidationError):
            config = self._make_config(**{'field': 'abc'})
            ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize('field_to_remove', [
        'image', 'flags', 'queue', 'task_name', 'warehouse_path'
    ])
    def test_missing_field(self, field_to_remove):
        with pytest.raises(ValidationError):
            config = self._make_config()
            config.pop(field_to_remove)
            ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize('image_name', [DockerImageName.gutenberg, DockerImageName.phet])
    def test_non_empty_flags(self, image_name):
        """For gutenberg and phet offliner, there should be no flags"""
        with pytest.raises(ValidationError):
            image = {'name': image_name, 'tag': 'latest'}
            flags = {'field', 'extra'}
            config = self._make_config(image=image, flags=flags)
            ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize('value', ScheduleQueue.all())
    def test_queue_passing(self, value):
        config = self._make_config(**{'queue': value})
        ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize('value', [None, 123, '123', True, [], {}])
    def test_queue_failing(self, value):
        with pytest.raises(ValidationError):
            config = self._make_config(**{'queue': value})
            ScheduleConfigSchema().load(config)
