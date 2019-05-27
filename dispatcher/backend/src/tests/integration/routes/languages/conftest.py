import pytest

from common.mongo import Languages


@pytest.fixture()
def make_language(database):
    languages_id = []
    languages = Languages(database=database)

    def _make_language(code: str, name_en: str, name_native: str):
        language = {'code': code, 'name_en': name_en, 'name_native': name_native}

        languages.insert_one(language)
        languages_id.append(language['_id'])
        return language

    yield _make_language

    languages.delete_many({'_id': {'$in': languages_id}})


@pytest.fixture()
def languages(make_language):
    languages = [
        make_language(code='en', name_en='English', name_native='English'),
        make_language(code='fr', name_en='French', name_native='Français'),
        make_language(code='es', name_en='Spanish', name_native='Español'),
        make_language(code='zh', name_en='Chinese', name_native='中文'),
        make_language(code='ab', name_en='Abkhazian', name_native='Аҧсшәа'),
        make_language(code='ace', name_en='Achinese', name_native='Acèh'),
        make_language(code='ady', name_en='Adyghe', name_native='адыгабзэ'),
        make_language(code='af', name_en='Afrikaans', name_native='Afrikaans'),
        make_language(code='ak', name_en='Akan', name_native='Akan'),
        make_language(code='als', name_en='Alemannisch', name_native='Alemannisch'),
        make_language(code='am', name_en='Amharic', name_native='አማርኛ'),
        make_language(code='an', name_en='Aragonese', name_native='aragonés'),
        make_language(code='ang', name_en='Old English', name_native='Ænglisc'),
        make_language(code='ar', name_en='Arabic', name_native='العربية'),
        make_language(code='arc', name_en='Aramaic', name_native='ܐܪܡܝܐ'),
        make_language(code='arz', name_en='Egyptian Arabic', name_native='مصرى'),
        make_language(code='as', name_en='Assamese', name_native='অসমীয়া'),
        make_language(code='ast', name_en='Asturian', name_native='asturianu'),
        make_language(code='atj', name_en='Atikamekw', name_native='Atikamekw'),
        make_language(code='av', name_en='Avaric', name_native='авар'),
        make_language(code='ay', name_en='Aymara', name_native='Aymar aru'),
        make_language(code='az', name_en='Azerbaijani', name_native='azərbaycan'),
        make_language(code='azb', name_en='Azerbaijani', name_native='تۆرکجه'),
        make_language(code='ba', name_en='Bashkir', name_native='башҡортса'),
        make_language(code='bar', name_en='Bavarian', name_native='Boarisch'),
        make_language(code='bcl', name_en='Central Bikol', name_native='Bikol Central'),
        make_language(code='be', name_en='Belarusian', name_native='беларуская'),
    ]
    return languages
