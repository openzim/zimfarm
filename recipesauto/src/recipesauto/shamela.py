import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from recipesauto.constants import logger
from recipesauto.context import Context
from recipesauto.utils import check_zim_name

context = Context.get()

book_re = re.compile(r"https://shamela.ws/book/(\d*)")

# archive.org is a free, often overloaded nonprofit service and regularly
# has brief outages/connection failures ; retry rather than let one bad
# request kill a whole run across dozens of categories
WAYBACK_RETRIES = 3
WAYBACK_RETRY_DELAY = 5


def _get_with_retries(url: str, **kwargs: Any) -> requests.Response:
    for attempt in range(1, WAYBACK_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=context.http_timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            if attempt == WAYBACK_RETRIES:
                raise
            logger.warning(
                f"Request to {url} failed ({exc}), retrying "
                f"({attempt}/{WAYBACK_RETRIES})..."
            )
            time.sleep(WAYBACK_RETRY_DELAY * attempt)
    raise AssertionError("unreachable")  # pragma: no cover


static_data = {
    "al-aqida": {
        "number": 1,
        "title": "العقيدة؛ المجموعة رقم 1",
        "description": "العقيدة الإسلامية وشروحاتها، والمتون وأصول الدين",
    },
    "al-firaq-wa-al-rudud": {
        "number": 2,
        "title": "الفرق والردود؛ المجموعة رقم 2",
        "description": "الفرق والأديان، والردود علي أهل الأهواء والبدع",
        "in_prod": True,
    },
    "al-tafsir": {
        "number": 3,
        "title": "التفسير؛ المجموعة رقم 3",
        "description": "تفاسير القرآن الكريم وتأويله",
    },
    "ulum-al-quran": {
        "number": 4,
        "title": "علوم القرآن؛ المجموعة رقم 4",
        "description": "أحكام القرآن، ومقدمات في أصول التفسير",
    },
    "al-tajwid-wa-al-qiraat": {
        "number": 5,
        "title": "التجويد؛ المجموعة رقم 5",
        "description": "التجويد وأصول القراءات والإبانة عن معانيها",
    },
    "al-sunna": {
        "number": 6,
        "title": "السنة النبوية؛ المجموعة رقم 6",
        "description": "الأحاديث النبوية، ومسانيد الأئمة",
    },
    "shuruh-al-hadith": {
        "number": 7,
        "title": "شروح الحديث؛ المجموعة رقم 7",
        "description": "شروحات الأحاديث النبوية والمسانيد",
    },
    "al-takhrij-wa-al-atraf": {
        "number": 8,
        "title": "التخريج؛ المجموعة رقم 8",
        "description": "تخريج الأحاديث والآثار، وبيان الضعيف والموضوع",
    },
    "al-ilal-wa-al-sualat": {
        "number": 9,
        "title": "علل الحديث؛ المجموعة رقم 9",
        "description": "علل الأحاديث ومعرفة الرجال والسؤالات",
        "in_prod": True,
    },
    "ulum-al-hadith": {
        "number": 10,
        "title": "علوم الحديث؛ المجموعة رقم 10",
        "description": "معرفة علوم الحديث وأصوله",
    },
    "usul-al-fiqh": {
        "number": 11,
        "title": "أصول الفقه؛ المجموعة رقم 11",
        "description": "الكتب والرسائل في أصول الفقه، وتقريب الوصول إليه",
    },
    "ulum-al-fiqh": {
        "number": 12,
        "title": "علوم الفقه؛ المجموعة رقم 12",
        "description": "علوم الفقه والقواعد الفقهية، ومعرفة الأشباه والنظائر في "
        "القواعد",
        "in_prod": True,
    },
    "al-mantiq": {
        "number": 13,
        "title": "المنطق؛ المجموعة رقم 13",
        "description": "المدخل إلي علم المنطق",
        "in_prod": True,
    },
    "al-fiqh-al-hanafi": {
        "number": 14,
        "title": "الفقه الحنفي؛ المجموعة رقم 14",
        "description": "فقه المذهب الحنفي",
        "in_prod": True,
    },
    "al-fiqh-al-maliki": {
        "number": 15,
        "title": "الفقه المالكي؛ المجموعة رقم 15",
        "description": "فقه المذهب المالكي",
        "in_prod": True,
    },
    "al-fiqh-al-shafii": {
        "number": 16,
        "title": "الفقه الشافعي؛ المجموعة رقم 16",
        "description": "فقه المذهب الشافعي",
        "in_prod": True,
    },
    "al-fiqh-al-hanbali": {
        "number": 17,
        "title": "الفقه الحنبلي؛ المجموعة رقم 17",
        "description": "فقه المذهب الحنبلي",
    },
    "al-fiqh-al-aam": {
        "number": 18,
        "title": "الفقه العام؛ المجموعة رقم 18",
        "description": "الفقه العام وأصوله",
    },
    "masail-fiqhiya": {
        "number": 19,
        "title": "مسائل فقهية؛ المجموعة رقم 19",
        "description": "المسائل الفقهية",
    },
    "al-siyasa-al-shariyya": {
        "number": 20,
        "title": "سياسة شرعية؛ المجموعة رقم 20",
        "description": "في السياسة الشرعية وبيان الاداب والأحكام",
        "in_prod": True,
    },
    "al-faraid-wa-al-wasaya": {
        "number": 21,
        "title": "الفرائض؛ المجموعة رقم 21",
        "description": "علم الفرائض والمواريث في الشريعة الإسلامية",
        "in_prod": True,
    },
    "al-fatawa": {
        "number": 22,
        "title": "الفتاوي؛ المجموعة رقم 22",
        "description": "مجموع رسائل وفتاوي العلماء في المسائل",
    },
    "al-raqaiq-wa-al-adhkar": {
        "number": 23,
        "title": "الأدب والزهد؛ المجموعة رقم 23",
        "description": "في الزهد والأخلاق، والآداب والأذكار، والحكم",
    },
    "al-sira-al-nabawiya": {
        "number": 24,
        "title": "السيرة؛ المجموعة رقم 24",
        "description": "في السيرة النبوية، ودلائل النبوة وأخبار الخلفاء",
    },
    "al-tarikh": {
        "number": 25,
        "title": "التاريخ؛ المجموعة رقم 25",
        "description": "التاريخ العربي والإسلامي",
    },
    "al-tarajim-wa-al-tabaqat": {
        "number": 26,
        "title": "التراجم؛ المجموعة رقم 26",
        "description": "السير وتراجم العلماء، وتاريخ البلدان وطبقات الأئمة",
    },
    "al-ansab": {
        "number": 27,
        "title": "الأنساب؛ المجموعة رقم 27",
        "description": "الأنساب والأخبار، ومعاجم في القبائل",
        "in_prod": True,
    },
    "al-buldan-wa-al-rihlat": {
        "number": 28,
        "title": "28 البلدان؛ المجموعة رقم",
        "description": "الرحلات والأسفار واستكشاف البلدان",
        "in_prod": True,
    },
    "al-lugha": {
        "number": 29,
        "title": "اللغة؛ المجموعة رقم 29",
        "description": "أصول اللغة العربية، ومعرفة الفروقات اللغوية والنوادر",
        "in_prod": True,
    },
    "al-gharib-wa-al-majim": {
        "number": 30,
        "title": "المعاجم؛ المجموعة رقم 30",
        "description": "معاجم في اللغة العربية، ومعرفة غرائب الكلمات",
    },
    "al-nahw-wa-al-sarf": {
        "number": 31,
        "title": "النحو والصرف؛ المجموعة رقم 31",
        "description": "النحو العربي وشروحاته، وعلم الصرف",
    },
    "al-adab": {
        "number": 32,
        "title": "الأدب العربي؛ المجموعة رقم 32",
        "description": "الأدب العربي",
    },
    "al-urud-wa-al-qawafi": {
        "number": 33,
        "title": "العروض؛ المجموعة رقم 33",
        "description": "علم العروض والقوافي",
    },
    "al-shir-wa-dawawinu": {
        "number": 34,
        "title": "دواوين الشعر؛ المجموعة رقم 34",
        "description": "دواوين الشعر العربي في الجاهلية وصدر الإسلام، وبعض الشروحات "
        "عليها",
        "disk": 536870912,
        "in_prod": True,
    },
    "al-balagha": {
        "number": 35,
        "title": "البلاغة؛ المجموعة رقم 35",
        "description": "علم البلاغة وأسرارها، ودلائل الإعجاز",
        "in_prod": True,
    },
    "al-jawami": {
        "number": 36,
        "title": "الجوامع؛ المجموعة رقم 36",
        "description": "جمع مؤلفات بعض العلماء في  كتاب أو مجلد واحد",
    },
    "al-faharis-wa-al-adilla": {
        "number": 37,
        "title": "فهارس الكتب؛ المجموعة رقم 37",
        "description": "جمع أسماء مؤلفات بعض العلماء",
    },
    "al-tib": {
        "number": 38,
        "title": "الطب؛ المجموعة رقم 38",
        "description": "الطب النبوي والعربي",
    },
    "kutub-amma": {
        "number": 39,
        "title": "كتب عامة؛ المجموعة رقم 39",
        "description": "كتب عامة في جميع الفنون",
    },
    "ulum-ukhra": {
        "number": 40,
        "title": "علوم أخري؛ المجموعة رقم 40",
        "description": "علوم أخري مثل، تعبير الرؤي وتفسير الأحلام، والفلسفة",
    },
}


def get_recipe_tag() -> str:
    return "shamela"


def _get_wayback_snapshot_url(url: str) -> str:
    """Get the URL of the closest Internet Archive Wayback Machine snapshot of url"""
    resp = _get_with_retries(
        "https://archive.org/wayback/available", params={"url": url}
    )
    snapshot = resp.json().get("archived_snapshots", {}).get("closest")
    if not snapshot:
        raise Exception(f"No Internet Archive snapshot found for {url}")
    # the API suggests a plain http:// URL even though web.archive.org fully
    # supports https ; force it, as some networks block outbound port 80
    return snapshot["url"].replace("http://", "https://", 1)


def _get_category_include_regex(category: int):
    # shamela.ws rejects all automated requests outright with a 403 (even
    # with a browser-like User-Agent, which works around similar blocks on
    # other sites) ; fetch the category page from the Internet Archive
    # Wayback Machine instead, which still has it indexed. This means book
    # listings can lag behind shamela.ws's current content by however old
    # the latest snapshot is.
    category_url = f"https://shamela.ws/category/{category}"
    resp = _get_with_retries(_get_wayback_snapshot_url(category_url))

    soup = BeautifulSoup(resp.text, "lxml")

    links = soup.find_all("a")
    books: list[str] = []
    for link in links:
        # the Wayback Machine rewrites hrefs with its own "/web/<ts>/" prefix,
        # so search for the real URL anywhere in the href, rather than
        # anchoring the match at the start of the string
        if match := book_re.search(link["href"]):
            book = match.group(1)
            books.append(book)

    return (
        f"^https:\\/\\/shamela\\.ws\\/(book\\/({'|'.join(books)})($|\\/.*)"
        f"|category\\/{category}|author\\/.+)"
    )


def get_expected_recipes() -> list[dict[str, Any]]:
    return [
        {
            "category": "other",
            "config": {
                "artifacts_globs": ["**/*.warc.gz"],
                "offliner": {
                    "adminEmail": "contact+zimfarm@kiwix.org",
                    "custom-css": context.assets / "shamela" / "shamela.ws.css",
                    "description": category_data["description"],
                    "failOnFailedSeed": True,
                    "failOnInvalidStatus": True,
                    "favicon": context.assets / "shamela" / "shamela_48.png",
                    "keep": True,
                    "mobileDevice": "Pixel 2",
                    "name": check_zim_name(f"shamela.ws_ar_{category_key}"),
                    "output": "/output",
                    "publisher": "openZIM",
                    "scopeIncludeRx": _get_category_include_regex(
                        category_data["number"]
                    ),
                    "scopeType": "custom",
                    "seeds": f"https://shamela.ws/category/{category_data['number']}",
                    "title": category_data["title"],
                    "workers": "4",
                    "zim-lang": "ara",
                    "zimit-progress-file": "/output/task_progress.json",
                    "offliner_id": "zimit",
                },
                "image": {
                    "name": "ghcr.io/openzim/zimit",
                    "tag": "3.1.3",
                },
                "monitor": False,
                "platform": "shamela",
                "resources": {
                    "cpu": 3,
                    "disk": category_data.get("disk", 107374182400),  # 100G by default
                    "memory": 4294967296,
                    "shm": 1073741824,
                },
                "warehouse_path": (
                    "/zimit" if category_data.get("in_prod", False) else "/.hidden/dev"
                ),
            },
            "enabled": False,
            "language": "ara",
            "name": f"shamela.ws_ar_{category_key}-{category_data['number']}",
            "periodicity": (
                "quarterly" if category_data.get("in_prod", False) else "manually"
            ),
            "tags": [
                "shamela",
            ],
            "archived": False,
            "context": "",
            "offliner": "zimit",
            "version": "3.1.3",
        }
        for category_key, category_data in static_data.items()
        if _is_needed(category_key, category_data)
    ]


def _is_needed(category_key: Any, category_data: Any) -> bool:  # noqa: ARG001
    return True
    # return category_data["number"] in [1, 2, 3, 4, 5, 6, 34]
    # return category_data["number"] == 1
