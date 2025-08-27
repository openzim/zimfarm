import pycountry
from sqlalchemy import select

from zimfarm_backend import logger
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Schedule


# Model of language that conforms to the pycountry.languages.Language model
class Language(BaseModel):
    name: str
    alpha_3: str


# For languages in the DB that we can't find in pycountry, we can use this map to
# normalize the language code. The key represents the language code in the DB.
# For each value, the name represents the name of the language in the DB and the
# alpha_3 represents the ISO 639-3 code of the language. So, the actual name of the
# language might vary from the name in the DB when we rely on pycountry for the name
normalization_map: dict[str, Language] = {
    "bat-smg": Language(name="Samogitian", alpha_3="sgs"),
    # There is no ISO 639-3 code for Belarusian (Taraškievica orthography)
    # "be-x-old": Language(name="Belarusian (Taraškievica orthography)", alpha_3=...)
    "bh": Language(name="Bhojpuri", alpha_3="bho"),
    "cbk-zam": Language(name="Chavacano", alpha_3="cbk"),
    "nds-nl": Language(name="Low Saxon", alpha_3="nds"),
    # Emiliano-Romagnolo  ISO 639-3 code has been deprecated as the ethnicities have
    # been split into Emilian and Romagnolo. What should we default to? egl for Emilian
    # or rgn for Romagnol?
    "fiu-vro": Language(name="Võro", alpha_3="vro"),
    "in": Language(name="Indonesian", alpha_3="ind"),
    "iw": Language(name="Hebrew", alpha_3="heb"),
    "mo": Language(name="Romanian", alpha_3="ron"),
    # Some languages in the DB are families of languages, so we can't use a single
    # language code. What should we default to? Such languages include:
    #  - Mayan languages
    #  - Nahuati and Nahuatl langauges
    #  - North American Indian languages
    "roa-rup": Language(name="Aromanian", alpha_3="rup"),
    "roa-tara": Language(name="Tarantino", alpha_3="nap"),
    # some languages are unknown in the db. Such languages include:
    # - Unknown language [ef]
    # - Unknown language [sp]
    "zh-classical": Language(name="Classical Chinese", alpha_3="lzh"),
    "zh-min-nan": Language(name="Chinese (Min Nan)", alpha_3="nan"),
    "zh-yue": Language(name="Cantonese", alpha_3="yue"),
}


def update_schedule_language_codes():
    """Update schedule language codes to be the ISO 639-3 codes"""
    with Session.begin() as session:
        for schedule in session.scalars(select(Schedule)):
            # Attempt to get the language code from the ISO 639-3 code
            language = pycountry.languages.get(alpha_3=schedule.language_code)
            # If not found, attempt to get the language code from the ISO 639-1 code
            if not language:
                language = pycountry.languages.get(alpha_2=schedule.language_code)

            if not language:
                language = normalization_map.get(schedule.language_code)

            if not language:
                logger.info(f"Language code {schedule.language_code} not found.")
                continue

            if schedule.language_code != language.alpha_3:
                logger.info(
                    f"Updating schedule language code {schedule.language_code} to "
                    f"{language.alpha_3}"
                )

            # Normalize the language code to the ISO 639-3 code
            schedule.language_code = language.alpha_3
            session.add(schedule)


if __name__ == "__main__":
    update_schedule_language_codes()
