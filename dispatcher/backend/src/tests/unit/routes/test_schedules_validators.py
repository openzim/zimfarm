import pytest

from routes.schedules.validators import mwoffliner_flags_validator


class TestMWOfflinerFlagsValidator:
    def make_mwoffilner_flags(self, mw_url='https://www.wikipedia.org', admin_email='contact@kiwix.org'):
        return {
            'mwUrl': mw_url,
            'adminEmail': admin_email
        }


    def test_invalid_mwUrl(self):
        flags = self.make_mwoffilner_flags()
        mwoffliner_flags_validator.check(flags)