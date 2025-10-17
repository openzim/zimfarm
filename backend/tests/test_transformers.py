# ruff: noqa: E501
from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest
from _pytest.python_api import RaisesContext

from zimfarm_backend.common.enums import DockerImageName
from zimfarm_backend.common.schemas.offliners.builder import generate_similarity_data
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
    SimilarityDataSchema,
    TransformerSchema,
)
from zimfarm_backend.common.schemas.offliners.transformers import transform_data
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
