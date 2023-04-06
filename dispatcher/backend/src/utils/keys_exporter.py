import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class KeysExporter:
    @staticmethod
    def _get_keys_int(obj, curPrefix):
        if isinstance(obj, Dict):
            for k, v in obj.items():
                yield f"{curPrefix}{k}"
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}{k}.")
        elif isinstance(obj, List):
            for v in obj:
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}*.")

    @staticmethod
    def get_keys(obj) -> List[str]:
        return set(KeysExporter._get_keys_int(obj, ""))
