from dataclasses import dataclass
from typing import Any


@dataclass
class Definition:
    schedule_name: str
    periodicity: str
    flags: dict[str, Any]
