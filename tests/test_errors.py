"""Unit tests for the DomainError hierarchy."""

import pytest

from brew.errors import (
    AuthFailedError,
    CloudUnreachableError,
    DomainError,
    NotFoundError,
    SlotLimitError,
    UnknownError,
    ValidationError,
)


def test_domain_error_is_exception():
    err = DomainError(message="boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"


def test_domain_error_code_derived_from_class_name():
    assert ValidationError(message="x").code == "validation"
    assert NotFoundError(message="x").code == "not_found"
    assert SlotLimitError(message="x").code == "slot_limit"
    assert CloudUnreachableError(message="x").code == "cloud_unreachable"
    assert AuthFailedError(message="x").code == "auth_failed"
    assert UnknownError(message="x").code == "unknown"


def test_validation_error_carries_typed_context():
    err = ValidationError(message="bad title", field="title", reason="empty")
    assert err.field == "title"
    assert err.reason == "empty"


def test_not_found_error_carries_typed_context():
    err = NotFoundError(message="missing", resource_kind="profile", resource_id="p42")
    assert err.resource_kind == "profile"
    assert err.resource_id == "p42"


def test_slot_limit_error_carries_typed_context():
    err = SlotLimitError(message="full", used=4, max=4, slot_kind="profile")
    assert err.used == 4
    assert err.max == 4
    assert err.slot_kind == "profile"


def test_cloud_unreachable_error_is_retryable():
    assert CloudUnreachableError.is_retryable is True


def test_other_errors_are_not_retryable():
    assert ValidationError.is_retryable is False
    assert NotFoundError.is_retryable is False
    assert SlotLimitError.is_retryable is False
    assert AuthFailedError.is_retryable is False
    assert UnknownError.is_retryable is False


def test_cloud_unreachable_error_carries_upstream_context():
    err = CloudUnreachableError(message="down", upstream_url="https://fellow.example/api", original="ConnectionError")
    assert err.upstream_url == "https://fellow.example/api"
    assert err.original == "ConnectionError"


def test_errors_can_be_raised_and_caught():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError(message="boom", field="x", reason="y")
    assert isinstance(exc_info.value, DomainError)
    assert exc_info.value.field == "x"
