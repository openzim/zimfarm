# ruff: noqa: T201
import io
import os
import shutil
import zipfile
from pathlib import Path

import httpx

FASTAPI_URL = "http://localhost:8000"
EXPORT_DIR = "docs_v2"
OPENAPI_FILE = os.path.join(EXPORT_DIR, "openapi.json")


def fetch_openapi():
    print("Fetching OpenAPI schema...")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    resp = httpx.get(f"{FASTAPI_URL}/openapi.json")
    resp.raise_for_status()
    with open(OPENAPI_FILE, "w") as f:
        f.write(resp.text)
    print(f"Saved to {OPENAPI_FILE}")


def download_swagger_ui_dist():
    print("Downloading Swagger UI dist/ folder...")

    zip_url = "https://github.com/swagger-api/swagger-ui/archive/refs/heads/master.zip"
    target_path = Path(EXPORT_DIR) / "swagger-ui"

    if (target_path / "dist").exists():
        print("Swagger UI dist/ already exists. Skipping download.")
        return

    # Download ZIP
    response = httpx.get(zip_url, follow_redirects=True)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        dist_members = [
            m for m in zip_file.namelist() if "swagger-ui-master/dist/" in m
        ]
        zip_file.extractall(EXPORT_DIR, members=dist_members)

    # Move dist/ folder to clean path
    extracted_dist = Path(EXPORT_DIR) / "swagger-ui-master" / "dist"
    final_dist = target_path / "dist"
    final_dist.parent.mkdir(parents=True, exist_ok=True)
    extracted_dist.rename(final_dist)

    # Clean up extracted base folder
    extracted_root = Path(EXPORT_DIR) / "swagger-ui-master"
    if extracted_root.exists():
        for item in extracted_root.iterdir():
            if item.is_dir():
                item.rmdir()
        extracted_root.rmdir()

    print(f"Swagger UI dist/ ready at {final_dist}")


def generate_swagger_ui():
    print("Cloning Swagger UI...")
    download_swagger_ui_dist()
    swagger_ui_repo = Path(EXPORT_DIR) / "swagger-ui"

    swagger_ui_dist = swagger_ui_repo / "dist"
    initializer_path = swagger_ui_dist / "swagger-initializer.js"

    print("Updating swagger-initializer.js...")
    initializer_path.write_text(
        """
window.onload = function() {
  window.ui = SwaggerUIBundle({
    url: "openapi.json",
    dom_id: '#swagger-ui',
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    layout: "StandaloneLayout"
  });
};
""".strip()
    )

    print("Copying openapi.json to Swagger UI directory...")
    shutil.copy(OPENAPI_FILE, swagger_ui_dist / "openapi.json")

    print(f"Swagger UI is ready at {swagger_ui_dist}")


if __name__ == "__main__":
    fetch_openapi()
    generate_swagger_ui()
