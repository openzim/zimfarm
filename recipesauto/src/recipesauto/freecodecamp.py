from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
import shutil
from typing import Any
import zipfile

import requests

from recipesauto.context import Context
from recipesauto.constants import logger
from recipesauto.utils import check_zim_name

context = Context.get()

FCC_MAIN_ZIP = (
    "https://github.com/freeCodeCamp/freeCodeCamp/archive/refs/heads/main.zip"
)


@dataclass
class Course:
    dashed_name: str
    order: int


@dataclass
class Curriculum:
    dashed_name: str
    courses: list[Course]


class SpokenLanguage(Enum):
    CHINESE = 1
    CHINESE_TRADITIONAL = 2
    ENGLISH = 3
    ESPANOL = 4
    GERMAN = 5
    ITALIAN = 6
    JAPANESE = 7
    KOREAN = 8
    PORTUGUESE = 9
    SWAHILI = 10
    UKRANIAN = 11


static_data = {
    "freecodecamp_en_javascript-algorithms-and-data-structures": {
        "title": "freeCodeCamp JavaScript",
        "description": "JavaScript courses",
        "long_description": "In the JavaScript Algorithm and Data Structures Certification, you'll learn the fundamentals of JavaScript including variables, arrays, objects, loops, and functions.",
    },
    "freecodecamp_es_javascript-algorithms-and-data-structures": {
        "title": "FreeCodeCamp JavaScript",
        "description": "Cursos de JavaScript",
        "long_description": "En la Certificación de estructuras de datos y algoritmos de JavaScript, aprenderá los fundamentos de JavaScript, incluidas variables, matrices, objetos, bucles y funciones.",
    },
    "freecodecamp_de_javascript-algorithms-and-data-structures": {
        "title": "FreeCodeCamp JavaScript",
        "description": "JavaScript-Kurse",
        "long_description": "In der Zertifizierung „JavaScript-Algorithmus und Datenstrukturen“ lernen Sie die Grundlagen von JavaScript, einschließlich Variablen, Arrays, Objekte, Schleifen und Funktionen.",
    },
    "freecodecamp_it_javascript-algorithms-and-data-structures": {
        "title": "FreeCodeCamp JavaScript",
        "description": "Corsi JavaScript",
        "long_description": "Nella certificazione sugli algoritmi JavaScript e sulle strutture dati imparerai i fondamenti di JavaScript, tra cui variabili, array, oggetti, loop e funzioni.",
    },
    "freecodecamp_ja_javascript-algorithms-and-data-structures": {
        "title": "FreeCodeCamp JavaScript",
        "description": "JavaScriptコース",
        "long_description": "JavaScript アルゴリズムおよびデータ構造認定では、変数、配列、オブジェクト、ループ、関数などの JavaScript の基礎を学びます",
    },
    "freecodecamp_pt_javascript-algorithms-and-data-structures": {
        "title": "FreecodeCamp JavaScript",
        "description": "Cursos JavaScript",
        "long_description": "Na Certificação de Algoritmo JavaScript e Estruturas de Dados, você aprenderá os fundamentos do JavaScript, incluindo variáveis, arrays, objetos, loops e funções.",
    },
    "freecodecamp_ua_javascript-algorithms-and-data-structures": {
        "title": "FreeCodeCamp JavaScript",
        "description": "Курси Javascript",
        "long_description": "Під час сертифікації JavaScript Algorithm and Data Structures Certification ви дізнаєтесь про основи JavaScript, зокрема про змінні, масиви, об’єкти, цикли та функції.",
    },
    "freecodecamp_en_coding-interview-prep": {
        "title": "FreeCodeCamp Interview Prep",
        "description": "Coding exercises",
        "long_description": "Dozens of coding challenges that test your knowledge of algorithms, data structures, and mathematics. It also has a number of take-home projects you can use to strengthen your skills, or add to your portfolio.",
    },
    "freecodecamp_it_coding-interview-prep": {
        "title": "Intervista di FreeCodeCamp",
        "description": "Esercizi di codifica",
        "long_description": "Decine di sfide di codifica che mettono alla prova la tua conoscenza di algoritmi, strutture dati e matematica. Ha anche una serie di progetti da portare a casa che puoi utilizzare per rafforzare le tue capacità o aggiungere al tuo portfolio.",
    },
    "freecodecamp_ja_coding-interview-prep": {
        "title": "FreeCodeCamp の面接準備",
        "description": "コーディング演習",
        "long_description": "アルゴリズム、データ構造、数学の知識をテストする数十のコーディング課題。また、スキルを強化したり、ポートフォリオに追加したりできる、持ち帰り用のプロジェクトも多数あります",
    },
    "freecodecamp_pt_coding-interview-prep": {
        "title": "Entrevista FreeCodeCamp",
        "description": "Exercícios de codificação",
        "long_description": "Dezenas de desafios de codificação que testam seu conhecimento de algoritmos, estruturas de dados e matemática. Ele também possui vários projetos para levar para casa que você pode usar para fortalecer suas habilidades ou adicionar ao seu portfólio.",
    },
    "freecodecamp_ua_coding-interview-prep": {
        "title": "Iнтерв’ю FreeCodeCamp",
        "description": "Вправи з кодування",
        "long_description": "Десятки завдань кодування, які перевіряють ваші знання алгоритмів, структур даних і математики. У ньому також є кілька проектів, які можна використати для вдосконалення ваших навичок або додати до свого портфоліо.",
    },
    "freecodecamp_en_project-euler": {
        "title": "Project Euler",
        "description": "Programming challenges",
        "long_description": "These problems will harden your algorithm and mathematics knowledge. They range in difficulty and, for many, the experience is inductive chain learning as solving one problem will expose you to a new concept that allows you to undertake a previously inaccessible challenge",
    },
    "freecodecamp_it_project-euler": {
        "title": "Progetto Eulero",
        "description": "Sfide di programmazione",
        "long_description": "Questi problemi rafforzeranno le tue conoscenze di algoritmi e matematica. Variano in termini di difficoltà e, per molti, l'esperienza è un apprendimento a catena induttivo poiché risolvere un problema ti esporrà a un nuovo concetto che ti consentirà di intraprendere una sfida precedentemente inaccessibile",
    },
    "freecodecamp_ja_project-euler": {
        "title": "プロジェクト・オイラー",
        "description": "プログラミングの課題",
        "long_description": "これらの問題は、アルゴリズムと数学の知識を強化します。難易度はさまざまで、多くの人にとって、1 つの問題を解決することで、これまでアクセスできなかった課題に取り組むことができる新しい概念に触れることができるため、その経験は帰納的連鎖学習です。",
    },
    "freecodecamp_pt_project-euler": {
        "title": "Projeto Euler",
        "description": "Desafios de programação",
        "long_description": "Esses problemas fortalecerão seu algoritmo e conhecimento matemático. Eles variam em dificuldade e, para muitos, a experiência é uma aprendizagem em cadeia indutiva, pois a resolução de um problema irá expô-lo a um novo conceito que lhe permitirá enfrentar um desafio anteriormente inacessível.",
    },
    "freecodecamp_ua_project-euler": {
        "title": "Проект Ейлера",
        "description": "Проблеми програмування",
        "long_description": "Ці завдання зміцнять ваш алгоритм і знання математики. Вони різняться за складністю, і для багатьох досвід є індуктивним ланцюговим навчанням, оскільки розв’язання однієї проблеми відкриє вам нову концепцію, яка дозволить вам взятися за завдання, яке раніше було недоступним",
    },
    "freecodecamp_en_rosetta-code": {
        "title": "Rosetta Code",
        "description": "Level up your creative problem solving skills",
        "long_description": "These challenges can prove to be difficult, but they will push your algorithm logic to new heights.",
    },
    "freecodecamp_es_rosetta-code": {
        "title": "Código Rosetta",
        "description": "Mejora tus habilidades creativas para resolver problemas",
        "long_description": "Estos desafíos pueden resultar difíciles, pero llevarán la lógica de su algoritmo a nuevas alturas.",
    },
    "freecodecamp_de_rosetta-code": {
        "title": "Rosetta-Code",
        "description": "Verbessern Sie Ihre kreativen Fähigkeiten zur Problemlösung",
        "long_description": "Diese Herausforderungen können sich als schwierig erweisen, aber sie werden Ihre Algorithmuslogik auf ein neues Niveau heben.",
    },
    "freecodecamp_ja_rosetta-code": {
        "title": "ロゼッタコード",
        "description": "創造的な問題解決スキルをレベルアップする",
        "long_description": "これらの課題は難しいことが判明する可能性がありますが、アルゴリズムのロジックを新たな高みに押し上げるでしょう。",
    },
    "freecodecamp_pt_rosetta-code": {
        "title": "Código Roseta",
        "description": "Aumente o nível de suas habilidades criativas de resolução de problemas",
        "long_description": "Esses desafios podem ser difíceis, mas levarão a lógica do seu algoritmo a novos patamares.",
    },
    "freecodecamp_sw_rosetta-code": {
        "title": "Kanuni ya Rosetta",
        "description": "Ongeza ujuzi wako wa ubunifu wa kutatua matatizo",
        "long_description": "Changamoto hizi zinaweza kuwa ngumu, lakini zitasukuma mantiki yako ya algorithm kufikia urefu mpya.",
    },
    "freecodecamp_ua_rosetta-code": {
        "title": "Кодекс Розетти",
        "description": "Розвивайте свої навички творчого вирішення проблем",
        "long_description": "Ці виклики можуть виявитися складними, але вони піднімуть логіку вашого алгоритму на нові висоти.",
    },
    "freecodecamp_it_rosetta-code": {
        "title": "Codice Rosetta",
        "description": "Migliora le tue capacità creative di risoluzione dei problemi",
        "long_description": "Queste sfide possono rivelarsi difficili, ma spingeranno la logica del tuo algoritmo a nuovi livelli.",
    },
}


def get_recipe_tag() -> str:
    return "freecodecamp"


def get_expected_recipes() -> list[dict[str, Any]]:

    work_folder = Path("fcc_work")
    if work_folder.exists():
        shutil.rmtree(work_folder)
    work_folder.mkdir(exist_ok=True)

    zip_path = work_folder / "fcc_repo.zip"
    extract_folder = work_folder / "extract"

    resp = requests.get(
        FCC_MAIN_ZIP,
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()
    zip_path.write_bytes(resp.content)
    del resp

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        count = 0
        for member in zip_ref.namelist():
            if not member.endswith("/") and (
                member.startswith("freeCodeCamp-main/curriculum/challenges/_meta")
                or member == "freeCodeCamp-main/shared/config/curriculum.ts"
            ):
                target_path = extract_folder / member[len("freeCodeCamp-main/") :]
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(zip_ref.read(member))

    curriculums: dict[str, Curriculum] = {}
    for meta_file in extract_folder.rglob("**/meta.json"):
        meta_content = json.loads(meta_file.read_bytes())
        curriculum_name = meta_content["superBlock"]
        if curriculum_name not in curriculums:
            curriculums[curriculum_name] = Curriculum(
                dashed_name=curriculum_name, courses=[]
            )
        curriculum = curriculums[curriculum_name]

        curriculum.courses.append(
            Course(
                dashed_name=meta_content["dashedName"],
                order=meta_content.get("order", 0),
            )
        )

    curriculum_ts = list(extract_folder.rglob("**/curriculum.ts"))[0]

    # map enum to slug, e.g. RespWebDesignNew => 2022/responsive-web-design
    curriculum_map: dict[str, str] = {}

    # dictionary of lang => list of not audited curriculum slug
    not_audited_curriculum: dict[SpokenLanguage, list[str]] = {}

    is_super_blocks_enum = is_not_audited_super_blocks = False
    current_language: SpokenLanguage | None = None
    for line in curriculum_ts.read_text().splitlines():
        if line.strip() == "}":
            is_super_blocks_enum = is_not_audited_super_blocks = False
        if line.strip() == "export enum SuperBlocks {":
            is_super_blocks_enum = True
        if (
            line.strip()
            == "export const notAuditedSuperBlocks: NotAuditedSuperBlocks = {"
        ):
            is_not_audited_super_blocks = True
        if is_not_audited_super_blocks:
            if match := re.match(r".*\[Languages\.(.*)\]:.*", line):
                if match.group(1) == "English":
                    current_language = SpokenLanguage.ENGLISH
                elif match.group(1) == "Espanol":
                    current_language = SpokenLanguage.ESPANOL
                elif match.group(1) == "Chinese":
                    current_language = SpokenLanguage.CHINESE
                elif match.group(1) == "ChineseTraditional":
                    current_language = SpokenLanguage.CHINESE_TRADITIONAL
                elif match.group(1) == "Italian":
                    current_language = SpokenLanguage.ITALIAN
                elif match.group(1) == "Portuguese":
                    current_language = SpokenLanguage.PORTUGUESE
                elif match.group(1) == "Ukrainian":
                    current_language = SpokenLanguage.UKRANIAN
                elif match.group(1) == "Japanese":
                    current_language = SpokenLanguage.JAPANESE
                elif match.group(1) == "German":
                    current_language = SpokenLanguage.GERMAN
                elif match.group(1) == "Swahili":
                    current_language = SpokenLanguage.SWAHILI
                elif match.group(1) == "Korean":
                    current_language = SpokenLanguage.KOREAN
                else:
                    raise Exception(
                        f"Unknown language found in curriculum.ts: {match.group(1)}"
                    )
                not_audited_curriculum[current_language] = []
            if match := re.match(r".*SuperBlocks\.(.*),.*", line):
                superblock = match.group(1)
                if superblock not in curriculum_map:
                    print(curriculum_map)
                    raise Exception(
                        f"Unknown superblock found in curriculum.ts: '{superblock}'"
                    )
                not_audited_curriculum[current_language].append(
                    curriculum_map[superblock]
                )
        if is_super_blocks_enum:
            if match := re.match(r"\s*(.*?)\s*=\s*'(.*)'.*", line):
                curriculum_map[match.group(1)] = match.group(2)

    return [
        {
            "category": "freecodecamp",
            "config": {
                "flags": {
                    "course": ",".join(
                        course.dashed_name
                        for course in sorted(
                            curriculum.courses, key=lambda course: course.order
                        )
                        # take-home-projects are not yet supported
                        if not course.dashed_name in ["take-home-projects"]
                    ),
                    "debug": True,
                    "description": _get_description(
                        curriculum=curriculum, language=language
                    ),
                    "language": _get_zim_language_metadata(language),
                    "long-description": _get_long_description(
                        curriculum=curriculum, language=language
                    ),
                    "name": check_zim_name(_get_name(curriculum=curriculum, language=language)),
                    "output": "/output",
                    "publisher": "openZIM",
                    "title": _get_title(curriculum=curriculum, language=language),
                },
                "image": {
                    "name": "ghcr.io/openzim/freecodecamp",
                    "tag": "1.3.0",
                },
                "monitor": False,
                "platform": None,
                "resources": {
                    "cpu": 1,
                    "disk": 536870912,
                    "memory": 2147483648,
                },
                "task_name": "freecodecamp",
                "warehouse_path": "/freecodecamp",
            },
            "enabled": True,
            "language": _get_zf_language(language=language),
            "name": _get_name(curriculum=curriculum, language=language),
            "periodicity": "quarterly",
            "tags": [
                "freecodecamp",
            ],
        }
        for curriculum in curriculums.values()
        for language in SpokenLanguage
        if _is_needed(curriculum=curriculum, language=language)
        and curriculum.dashed_name not in not_audited_curriculum[language]
    ]


class UndefinedMetadataError(Exception):
    pass

def _get_zf_language(language: SpokenLanguage) -> dict[str, str]:
    if language == SpokenLanguage.CHINESE:
        raise NotImplementedError()
    elif language == SpokenLanguage.CHINESE_TRADITIONAL:
        raise NotImplementedError()
    elif language == SpokenLanguage.ENGLISH:
        return {
            "code": "en",
            "name_en": "English",
            "name_native": "English",
        }
    elif language == SpokenLanguage.ESPANOL:
        return {
            "code": "es",
            "name_en": "Spanish",
            "name_native": "español",
        }
    elif language == SpokenLanguage.GERMAN:
        return {
            "code": "de",
            "name_en": "German",
            "name_native": "Deutsch",
        }
    elif language == SpokenLanguage.ITALIAN:
        return {
            "code": "it",
            "name_en": "Italian",
            "name_native": "italiano",
        }
    elif language == SpokenLanguage.JAPANESE:
        return {
            "code": "ja",
            "name_en": "Japanese",
            "name_native": "日本語",
        }
    elif language == SpokenLanguage.KOREAN:
        raise NotImplementedError()
    elif language == SpokenLanguage.PORTUGUESE:
        return {
            "code": "pt",
            "name_en": "Portuguese",
            "name_native": "português",
        }
    elif language == SpokenLanguage.SWAHILI:
        return {
            "code": "sw",
            "name_en": "Swahili",
            "name_native": "Kiswahili",
        }
    elif language == SpokenLanguage.UKRANIAN:
        return {
            "code": "uk",
            "name_en": "Ukrainian",
            "name_native": "українська",
        }


def _get_name(curriculum: Curriculum, language: SpokenLanguage) -> str:
    return f"freecodecamp_{_get_zim_name_lang(language)}_{curriculum.dashed_name}"


def _get_title(curriculum: Curriculum, language: SpokenLanguage) -> str:
    key = _get_name(curriculum=curriculum, language=language)
    title = static_data[key]["title"]
    if len(title) > 30:
        logger.warning(f"Title is too long for {key}")
    return title


def _get_description(curriculum: Curriculum, language: SpokenLanguage) -> str:
    key = _get_name(curriculum=curriculum, language=language)
    description = static_data[key]["description"]
    if len(description) > 80:
        logger.warning(f"Description is too long for {key}")
    return description


def _get_long_description(curriculum: Curriculum, language: SpokenLanguage) -> str:
    key = _get_name(curriculum=curriculum, language=language)
    long_description = static_data[key]["long_description"]
    if len(long_description) > 4000:
        logger.warning(f"LongDescription is too long for {key}")
    return long_description


def _get_zim_name_lang(language: SpokenLanguage) -> str:
    if language == SpokenLanguage.CHINESE:
        raise UndefinedMetadataError
    elif language == SpokenLanguage.CHINESE_TRADITIONAL:
        raise UndefinedMetadataError
    elif language == SpokenLanguage.ENGLISH:
        return "en"
    elif language == SpokenLanguage.ESPANOL:
        return "es"
    elif language == SpokenLanguage.GERMAN:
        return "de"
    elif language == SpokenLanguage.ITALIAN:
        return "it"
    elif language == SpokenLanguage.JAPANESE:
        return "ja"
    elif language == SpokenLanguage.KOREAN:
        return "ko"
    elif language == SpokenLanguage.PORTUGUESE:
        return "pt"
    elif language == SpokenLanguage.SWAHILI:
        return "sw"
    elif language == SpokenLanguage.UKRANIAN:
        return "ua"
    else:
        raise UndefinedMetadataError


def _get_zim_language_metadata(language: SpokenLanguage) -> str:
    if language == SpokenLanguage.CHINESE:
        raise UndefinedMetadataError
    elif language == SpokenLanguage.CHINESE_TRADITIONAL:
        raise UndefinedMetadataError
    elif language == SpokenLanguage.ENGLISH:
        return "eng"
    elif language == SpokenLanguage.ESPANOL:
        return "spa"
    elif language == SpokenLanguage.GERMAN:
        return "deu"
    elif language == SpokenLanguage.ITALIAN:
        return "ita"
    elif language == SpokenLanguage.JAPANESE:
        return "jpn"
    elif language == SpokenLanguage.KOREAN:
        return "kor"
    elif language == SpokenLanguage.PORTUGUESE:
        return "por"
    elif language == SpokenLanguage.SWAHILI:
        return "swa"
    elif language == SpokenLanguage.UKRANIAN:
        return "ukr"
    else:
        raise UndefinedMetadataError


def _is_needed(curriculum: Curriculum, language: SpokenLanguage) -> bool:
    return curriculum.dashed_name in [
        "javascript-algorithms-and-data-structures",
        "project-euler",
        "rosetta-code",
        "coding-interview-prep",
    ] and language not in [
        SpokenLanguage.CHINESE,  # not yet defined which code to use
        SpokenLanguage.CHINESE_TRADITIONAL,  # not yet defined which code to use
        SpokenLanguage.KOREAN,  # not yet officialy supported on website
    ]
