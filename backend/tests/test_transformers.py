# ruff: noqa: E501
from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest
from _pytest.python_api import RaisesContext
from pytest import MonkeyPatch

from zimfarm_backend.common.enums import DockerImageName
from zimfarm_backend.common.schemas.offliners import transformers as transformers_module
from zimfarm_backend.common.schemas.offliners.builder import (
    build_offliner_model,
    generate_similarity_data,
)
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
    SimilarityDataSchema,
    TransformerSchema,
)
from zimfarm_backend.common.schemas.offliners.transformers import (
    process_blob_fields,
    transform_data,
)
from zimfarm_backend.common.schemas.orms import OfflinerSchema


@pytest.mark.parametrize(
    "transformers,data,expected",
    [
        pytest.param(
            [TransformerSchema(name="split", operand=",")],
            ["a,b,c"],
            ["a", "b", "c"],
            id="split-operand-only",
        ),
        pytest.param(
            [TransformerSchema(name="hostname")],
            ["https://example.com"],
            ["example.com"],
            id="hostname-only",
        ),
        pytest.param(
            [
                TransformerSchema(name="split", operand=","),
                TransformerSchema(name="hostname"),
            ],
            ["https://example.com,https://example.org"],
            ["example.com", "example.org"],
            id="split-first-then-hostname",
        ),
        pytest.param(
            [
                TransformerSchema(name="hostname"),
                TransformerSchema(name="split", operand=","),
            ],
            ["https://example.com,https://example.org"],
            # hostname first returns example.com,https
            ["example.com", "https"],
            id="hostname-first-then-split",
        ),
    ],
)
def test_transform_data(
    transformers: list[TransformerSchema], data: list[str], expected: list[str]
):
    assert transform_data(data, transformers) == expected


@pytest.mark.parametrize(
    "similarity_data,data,expected_similarity_data",
    [
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seeds", transformers=[TransformerSchema(name="hostname")]
                )
            ],
            {
                "seeds": "https://www.mankier.com/stats",
            },
            ["www.mankier.com"],
            id="transform-seed-hostname",
        ),
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seed_file",
                    transformers=[
                        TransformerSchema(name="split", operand=","),
                        TransformerSchema(name="hostname"),
                    ],
                )
            ],
            {
                "seedFile": "https://www.mankier.com/stats,https://dart.dev/tutorials",
            },
            ["www.mankier.com", "dart.dev"],
            id="transform-seed-file-by-alias",
        ),
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seed_file",
                    transformers=[
                        TransformerSchema(name="split", operand=","),
                        TransformerSchema(name="hostname"),
                    ],
                )
            ],
            {
                "seedFile": "https://www.mankier.com/stats,https://dart.dev/tutorials",
            },
            ["www.mankier.com", "dart.dev"],
            id="transform-seed-file-by-flag-name",
        ),
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seed_file",
                    transformers=[
                        TransformerSchema(name="split", operand=","),
                        TransformerSchema(name="hostname"),
                    ],
                ),
                SimilarityDataSchema(
                    flag="seeds",
                    transformers=[
                        TransformerSchema(name="hostname"),
                    ],
                ),
            ],
            {
                "seeds": "https://www.mankier.com/stats",
                "seedFile": "https://dart.dev/tutorials",
            },
            ["www.mankier.com", "dart.dev"],
            id="transform-seed-file-by-flag-name-and-seeds",
        ),
    ],
)
def test_generate_similarity_data(
    similarity_data: list[SimilarityDataSchema],
    data: dict[str, Any],
    expected_similarity_data: str,
):
    spec = OfflinerSpecSchema.model_validate_json(
        """{
          "offliner_id": "zimit",
          "stdOutput": true,
          "stdStats": "zimit-progress-file",
          "flags": {
            "seeds": {
              "type": "string",
              "required": false,
              "title": "Seeds",
              "description": "The seed URL(s) to start crawling from. Multile seed URL must be separated by a comma (usually not needed, these are just the crawl seeds). First seed URL is used as ZIM homepage"
            },
            "seed_file": {
              "type": "string",
              "required": false,
              "title": "Seed File",
              "description": "If set, read a list of seed urls, one per line. HTTPS URL to an online file."
            }
          }
        }""",
    )
    spec.similarity_data = similarity_data
    offliner = OfflinerSchema(
        id="zimit",
        base_model="CamelModel",
        docker_image_name=DockerImageName.zimit,
        command_name="zimit2zim",
        ci_secret_hash=None,
    )
    results = generate_similarity_data(data, offliner, spec)
    assert len(results) == len(expected_similarity_data)
    for x in results:
        assert x in expected_similarity_data


@pytest.mark.parametrize(
    "similarity_data,data,expected",
    [
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seeds", transformers=[TransformerSchema(name="hostname")]
                )
            ],
            {
                "seeds": "https://www.mankier.com/stats",
            },
            does_not_raise(),
            id="transform-seed-hostname",
        ),
        pytest.param(
            [
                SimilarityDataSchema(
                    flag="seed_file",
                    transformers=[
                        TransformerSchema(name="split", operand=","),
                        TransformerSchema(name="hostname"),
                    ],
                ),
                SimilarityDataSchema(
                    flag="seeds",
                    transformers=[
                        TransformerSchema(name="hostname"),
                    ],
                ),
            ],
            {
                "seedFile": "https://dart.dev/tutorials",
            },
            does_not_raise(),
            id="transform-seed-file-but-missing-seeds-data",
        ),
    ],
)
def test_generate_similarity_data_value_missing(
    similarity_data: list[SimilarityDataSchema],
    data: dict[str, Any],
    expected: RaisesContext[Exception],
):
    spec = OfflinerSpecSchema.model_validate_json(
        """{
          "offliner_id": "zimit",
          "stdOutput": true,
          "stdStats": "zimit-progress-file",
          "flags": {
            "seeds": {
              "type": "string",
              "required": false,
              "title": "Seeds",
              "description": "The seed URL(s) to start crawling from. Multile seed URL must be separated by a comma (usually not needed, these are just the crawl seeds). First seed URL is used as ZIM homepage"
            },
            "seed_file": {
              "type": "string",
              "required": false,
              "title": "Seed File",
              "description": "If set, read a list of seed urls, one per line. HTTPS URL to an online file."
            }
          }
        }""",
    )
    spec.similarity_data = similarity_data
    offliner = OfflinerSchema(
        id="zimit",
        base_model="CamelModel",
        docker_image_name=DockerImageName.zimit,
        command_name="zimit2zim",
        ci_secret_hash=None,
    )
    with expected:
        generate_similarity_data(data, offliner, spec)


def test_process_blob_field(monkeypatch: MonkeyPatch):
    spec = OfflinerSpecSchema.model_validate(
        {
            "flags": {
                "custom_css": {
                    "type": "blob",
                    "kind": "css",
                    "label": "Custom CSS",
                    "description": "Upload custom CSS file",
                    "alias": "custom-css",
                    "required": False,
                },
                "name": {
                    "type": "string",
                    "label": "Name",
                    "description": "Project name",
                    "required": True,
                },
            }
        }
    )
    offliner = OfflinerSchema(
        id="zimit",
        base_model="CamelModel",
        docker_image_name=DockerImageName.zimit,
        command_name="zimit2zim",
        ci_secret_hash=None,
    )

    offliner_model = build_offliner_model(offliner, spec)
    instance = offliner_model.model_validate(
        {"offliner_id": "zimit", "name": "test", "custom-css": "base64string"}
    )
    monkeypatch.setattr(
        transformers_module, "BLOB_STORAGE_URL", "http://blob-storage.com"
    )
    processed_blobs = process_blob_fields(instance, spec)
    assert len(processed_blobs) == 1
    assert str(processed_blobs[0].url).startswith("http://blob-storage.com")
