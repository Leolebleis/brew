"""Integration tests for the DomainError -> HTTP response handler."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from brew.errors import (
    AuthFailedError,
    CloudUnreachableError,
    NotFoundError,
    SlotLimitError,
    UnknownError,
    ValidationError,
)
from brew.exception_handlers import register_exception_handlers


def _make_app_with_handler() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-validation")
    def raise_validation() -> dict:
        raise ValidationError(message="bad title", field="title", reason="empty")

    @app.get("/raise-not-found")
    def raise_not_found() -> dict:
        raise NotFoundError(message="missing", resource_kind="profile", resource_id="p42")

    @app.get("/raise-slot-limit")
    def raise_slot_limit() -> dict:
        raise SlotLimitError(message="full", used=4, max=4, slot_kind="profile")

    @app.get("/raise-cloud-unreachable")
    def raise_cloud() -> dict:
        raise CloudUnreachableError(message="down", upstream_url="https://x", original="timeout")

    @app.get("/raise-auth-failed")
    def raise_auth() -> dict:
        raise AuthFailedError(message="bad creds", reason="401 from fellow")

    @app.get("/raise-unknown")
    def raise_unknown() -> dict:
        raise UnknownError(message="weird", original="RuntimeError")

    return app


def test_validation_error_returns_400():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-validation")
    assert resp.status_code == 400
    assert resp.json() == {
        "error": {
            "code": "validation",
            "message": "bad title",
            "context": {"field": "title", "reason": "empty"},
        }
    }


def test_not_found_error_returns_404():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-not-found")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
    assert resp.json()["error"]["context"]["resource_id"] == "p42"


def test_slot_limit_error_returns_409():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-slot-limit")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "slot_limit"
    assert resp.json()["error"]["context"] == {"used": 4, "max": 4, "slot_kind": "profile"}


def test_cloud_unreachable_returns_503():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-cloud-unreachable")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "cloud_unreachable"


def test_auth_failed_returns_502():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-auth-failed")
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "auth_failed"


def test_unknown_returns_500():
    client = TestClient(_make_app_with_handler())
    resp = client.get("/raise-unknown")
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "unknown"
