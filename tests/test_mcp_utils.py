"""Unit tests for the shared MCP helpers."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastmcp.exceptions import ToolError

from brew.errors import NotFoundError
from brew.mcp_utils import (
    domain_error_to_resource_payload,
    domain_error_to_tool_error,
    jsonify,
)


@dataclass
class _Sample:
    id: str
    name: str


def test_domain_error_to_tool_error_produces_envelope() -> None:
    err = NotFoundError(
        message="Bag b1 not found",
        resource_kind="bag",
        resource_id="b1",
    )

    tool_err = domain_error_to_tool_error(err)

    assert isinstance(tool_err, ToolError)
    payload = json.loads(str(tool_err))
    assert payload == {
        "error": {
            "code": "not_found",
            "message": "Bag b1 not found",
            "context": {"resource_kind": "bag", "resource_id": "b1"},
        }
    }


def test_domain_error_to_resource_payload_returns_envelope_string() -> None:
    err = NotFoundError(
        message="Entry e9 not found",
        resource_kind="journal_entry",
        resource_id="e9",
    )

    payload = domain_error_to_resource_payload(err)

    assert isinstance(payload, str)
    assert json.loads(payload) == {
        "error": {
            "code": "not_found",
            "message": "Entry e9 not found",
            "context": {"resource_kind": "journal_entry", "resource_id": "e9"},
        }
    }


def test_jsonify_serializes_single_dataclass() -> None:
    sample = _Sample(id="s1", name="alpha")

    result = jsonify(sample)

    assert json.loads(result) == {"id": "s1", "name": "alpha"}


def test_jsonify_serializes_list_of_dataclasses() -> None:
    samples = [_Sample(id="s1", name="alpha"), _Sample(id="s2", name="beta")]

    result = jsonify(samples)

    assert json.loads(result) == [
        {"id": "s1", "name": "alpha"},
        {"id": "s2", "name": "beta"},
    ]


def test_jsonify_serializes_plain_dict() -> None:
    result = jsonify({"status": "ok", "count": 3})

    assert json.loads(result) == {"status": "ok", "count": 3}


def test_jsonify_serializes_none() -> None:
    assert jsonify(None) == "null"


def test_jsonify_uses_default_str_for_datetime() -> None:
    dt = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)

    @dataclass
    class _WithDt:
        when: datetime

    result = jsonify(_WithDt(when=dt))

    data = json.loads(result)
    assert isinstance(data["when"], str)
    assert "2026-04-19" in data["when"]


def test_jsonify_list_handles_mixed_non_dataclass_items() -> None:
    """Mixed lists (e.g., list of dicts) should still serialize cleanly."""
    result = jsonify([{"a": 1}, {"a": 2}])

    assert json.loads(result) == [{"a": 1}, {"a": 2}]


def test_jsonify_top_level_datetime_uses_default_str() -> None:
    dt = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)

    result = jsonify(dt)

    assert isinstance(json.loads(result), str)


@pytest.mark.parametrize(
    ("error_kwargs", "expected_code"),
    [
        ({"message": "not found", "resource_kind": "x", "resource_id": "y"}, "not_found"),
    ],
)
def test_domain_error_helpers_use_error_code(error_kwargs: dict, expected_code: str) -> None:
    err = NotFoundError(**error_kwargs)

    tool_err = domain_error_to_tool_error(err)
    resource_payload = domain_error_to_resource_payload(err)

    assert json.loads(str(tool_err))["error"]["code"] == expected_code
    assert json.loads(resource_payload)["error"]["code"] == expected_code
