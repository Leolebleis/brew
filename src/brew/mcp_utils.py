"""Shared MCP helpers — error envelope + JSON serialization.

All MCP tools/resources should run through these so the wire contract stays
identical across bounded contexts. Aiden contexts already follow this; bags/
journal/water didn't, so a NotFoundError there bubbled as a raw transport
error instead of the structured envelope.
"""

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from fastmcp.exceptions import ToolError

from brew.errors import DomainError
from brew.response_models import ErrorResponse


def domain_error_to_tool_error(exc: DomainError) -> ToolError:
    """Convert a DomainError to a ToolError carrying the standard envelope."""
    body = ErrorResponse.from_domain_error(exc)
    return ToolError(json.dumps({"error": body.model_dump()}))


def domain_error_to_resource_payload(exc: DomainError) -> str:
    """For MCP read_resource handlers — return the JSON envelope as a string body."""
    body = ErrorResponse.from_domain_error(exc)
    return json.dumps({"error": body.model_dump()})


def jsonify(value: Any) -> str:  # noqa: ANN401
    """Serialize a domain dataclass (or list of) to JSON.

    `default=str` handles datetime / date / enum-ish values that show up in
    snapshots. Pre-checks for dataclass-vs-list to avoid accidental double
    encoding.
    """
    if isinstance(value, list):
        return json.dumps(
            [asdict(item) if is_dataclass(item) else item for item in value],
            default=str,
        )
    if is_dataclass(value) and not isinstance(value, type):
        return json.dumps(asdict(value), default=str)
    return json.dumps(value, default=str)
