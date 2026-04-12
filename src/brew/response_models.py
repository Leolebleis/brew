"""Presentation-layer response models.

The DomainError hierarchy lives in the pure domain; its wire shape lives
here. Used by the FastAPI exception handler and by MCP tools.
"""

from dataclasses import fields

from pydantic import BaseModel

from brew.errors import DomainError


class ErrorResponse(BaseModel):
    """Wire format for domain errors. Used in REST response bodies and MCP ToolError payloads."""

    code: str
    message: str
    context: dict[str, object]

    @classmethod
    def from_domain_error(cls, err: DomainError) -> "ErrorResponse":
        context = {f.name: getattr(err, f.name) for f in fields(err) if f.name != "message"}
        return cls(code=err.code, message=err.message, context=context)
