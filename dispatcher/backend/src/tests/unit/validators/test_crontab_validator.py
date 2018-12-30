import pytest
import trafaret

from routes.schedules.validators import CrontabValidator

test_data = [
    ({'minute': '*', 'hour': '*', 'day_of_week': '*', 'day_of_month': '*', 'month_of_year': '*'},
     {'minute': '*', 'hour': '*', 'day_of_week': '*', 'day_of_month': '*', 'month_of_year': '*'}),
    ({'minute': '*', 'hour': '*'},
     {'minute': '*', 'hour': '*', 'day_of_week': '*', 'day_of_month': '*', 'month_of_year': '*'})
]


@pytest.mark.parametrize("test_input", [
    [],
    {'day_of_month': 10},
    {'hours': '*'},
    {'day_of_week': ''}
])
def test_invalid(test_input):
    with pytest.raises(trafaret.DataError):
        validator = CrontabValidator()
        validator.check(test_input)


@pytest.mark.parametrize("test_input, expected", test_data)
def test_valid(test_input, expected):
    validator = CrontabValidator()
    assert expected == validator.check(test_input)
