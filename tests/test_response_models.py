"""Unit tests for the ErrorResponse Pydantic model."""

from brew.errors import (
    CloudUnreachableError,
    NotFoundError,
    SlotLimitError,
    UnknownError,
    ValidationError,
)
from brew.response_models import ErrorResponse


def test_from_validation_error():
    err = ValidationError(message="bad", field="title", reason="empty")
    resp = ErrorResponse.from_domain_error(err)
    assert resp.code == "validation"
    assert resp.message == "bad"
    assert resp.context == {"field": "title", "reason": "empty"}


def test_from_not_found_error():
    err = NotFoundError(message="missing", resource_kind="profile", resource_id="p42")
    resp = ErrorResponse.from_domain_error(err)
    assert resp.code == "not_found"
    assert resp.context == {"resource_kind": "profile", "resource_id": "p42"}


def test_from_slot_limit_error():
    err = SlotLimitError(message="full", used=4, max=4, slot_kind="profile")
    resp = ErrorResponse.from_domain_error(err)
    assert resp.context == {"used": 4, "max": 4, "slot_kind": "profile"}


def test_from_cloud_unreachable_error():
    err = CloudUnreachableError(message="down", upstream_url="https://x", original="timeout")
    resp = ErrorResponse.from_domain_error(err)
    assert resp.code == "cloud_unreachable"
    assert resp.context == {"upstream_url": "https://x", "original": "timeout"}


def test_from_unknown_error_with_none_fields():
    err = UnknownError(message="weird")
    resp = ErrorResponse.from_domain_error(err)
    assert resp.code == "unknown"
    assert resp.context == {"original": None}


def test_model_dump_shape():
    err = ValidationError(message="bad", field="title", reason="empty")
    dumped = ErrorResponse.from_domain_error(err).model_dump()
    assert dumped == {
        "code": "validation",
        "message": "bad",
        "context": {"field": "title", "reason": "empty"},
    }
