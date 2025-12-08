import pytest
from pydantic import ValidationError

from zimfarm_backend.common.schemas.offliners.models import FlagSchema


def test_blob_type_with_valid_kind():
    """Test that blob type with kind is valid"""
    flag = FlagSchema(
        label="Logo Image",
        description="Upload a logo image",
        type="blob",
        kind="image",
    )
    assert flag.type == "blob"
    assert flag.kind == "image"


def test_blob_type_without_kind_raises_error():
    """Test that blob type without kind raises ValidationError"""
    with pytest.raises(ValidationError):
        FlagSchema(
            label="Some Blob",
            description="A blob without kind",
            type="blob",
        )


def test_non_blob_type_without_kind_valid():
    """Test that non-blob types without kind are valid"""
    flag = FlagSchema(
        label="Website URL",
        description="The URL to scrape",
        type="url",
    )
    assert flag.type == "url"
    assert flag.kind is None


def test_non_blob_type_with_kind_raises_error():
    """Test that non-blob type with kind raises ValidationError"""
    with pytest.raises(ValidationError):
        FlagSchema(
            label="Website URL",
            description="The URL to scrape",
            type="url",
            kind="image",
        )
