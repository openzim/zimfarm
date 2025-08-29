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
    # So, we use the nearest parent language => bel
    "be-x-old": Language(name="Belarusian (Taraškievica orthography)", alpha_3="bel"),
    "bh": Language(name="Bhojpuri", alpha_3="bho"),
    "cbk-zam": Language(name="Chavacano", alpha_3="cbk"),
    "nds-nl": Language(name="Low Saxon", alpha_3="nds"),
    # Emiliano-Romagnolo  ISO 639-3 code has been deprecated as the ethnicities have
    # been split into Emilian and Romagnolo. What should we default to? egl for Emilian
    # or rgn for Romagnol? For now, use mul
    "eml": Language(name="Emilian-Romagnol", alpha_3="mul"),
    "fiu-vro": Language(name="Võro", alpha_3="vro"),
    "in": Language(name="Indonesian", alpha_3="ind"),
    "iw": Language(name="Hebrew", alpha_3="heb"),
    "mo": Language(name="Romanian", alpha_3="ron"),
    # Some languages in the DB are families of languages, so we can't use a single
    # language code. What should we default to? Such languages include:
    #  - Mayan languages
    #  - Nahuati and Nahuatl langauges
    #  - North American Indian languages
    # Use mul for such languages
    "nah": Language(name="Nāhuatl", alpha_3="mul"),
    "myn": Language(name="Mayan Languages", alpha_3="mul"),
    "nai": Language(name="North American Indian Languages", alpha_3="mul"),
    "roa-rup": Language(name="Aromanian", alpha_3="rup"),
    "roa-tara": Language(name="Tarantino", alpha_3="nap"),
    "ef": Language(name="Unknown[ef]", alpha_3="efi"),  # Efik
    "sp": Language(name="Unknown[sp]", alpha_3="nso"),  # Sepedi
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
                pass
                # logger.info(
                #     f"Updating schedule language code {schedule.language_code} to "
                #     f"{language.alpha_3}"
                # )

            # Normalize the language code to the ISO 639-3 code
            schedule.language_code = language.alpha_3


if __name__ == "__main__":
    update_schedule_language_codes()
