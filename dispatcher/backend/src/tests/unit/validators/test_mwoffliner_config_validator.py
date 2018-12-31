import pytest
import trafaret

from routes.schedules.validators import MWOfflinerConfigValidator

test_data = [
    {'mwUrl': 'http://en.wikipedia.org', 'adminEmail': 'test@kiwix.org'},
    {'mwUrl': 'https://en.wikipedia.org', 'adminEmail': 'test@kiwix.org'}
]


@pytest.mark.parametrize("test_input", [
    [],
    {'mwUrl': 'https://en.wikipedia.org'},
    {'adminEmail': 'test@kiwix.org'},
    {'mwUrl': 'bad_url', 'adminEmail': 'test@kiwix.org'},
    {'mwURL': 'https://en.wikipedia.org', 'adminEmail': 'test@kiwix.org'},
    {'mwUrl': 'https://en.wikipedia.org', 'adminEmail': 'bad_email'},
])
def test_invalid_required(test_input):
    with pytest.raises(trafaret.DataError):
        validator = MWOfflinerConfigValidator()
        validator.check(test_input)


@pytest.mark.parametrize("test_input", test_data)
def test_valid(test_input):
    validator = MWOfflinerConfigValidator()
    validator.check(test_input)
