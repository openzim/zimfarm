import base64

import requests

from zimfarm_backend.common.constants import REQ_TIMEOUT_GHCR


def get_schedule_image_tags(hub_name: str) -> list[str]:
    token = base64.b64encode(f"v1:{hub_name}:0".encode()).decode()
    response = requests.get(
        f"https://ghcr.io/v2/{hub_name}/tags/list",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "Docker-Client/20.10.2 (linux)",
        },
        timeout=REQ_TIMEOUT_GHCR,
    )
    response.raise_for_status()
    return response.json()["tags"]
