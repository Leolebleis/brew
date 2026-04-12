"""Framework-agnostic domain error hierarchy.

Subclasses carry typed context fields. This module imports nothing from
FastAPI, Pydantic, or the Fellow library — it's the purest domain layer,
imported by infrastructure, application, and presentation alike.
"""

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class DomainError(Exception):
    """Base for all domain-layer errors.

    Non-frozen: frozen dataclasses conflict with Exception's __traceback__
    attribute assignment (CPython #117211). Treat instances as immutable by
    convention.
    """

    message: str

    def __post_init__(self) -> None:
        super().__init__(self.message)

    @property
    def code(self) -> str:
        """Stable machine-readable identifier derived from class name.

        ValidationError -> 'validation'
        SlotLimitError  -> 'slot_limit'
        """
        name = type(self).__name__.removesuffix("Error")
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    is_retryable: ClassVar[bool] = False


@dataclass
class ValidationError(DomainError):
    """Caller-supplied input failed validation."""

    field: str | None = None
    reason: str | None = None


@dataclass
class NotFoundError(DomainError):
    """A referenced resource does not exist."""

    resource_kind: str | None = None
    resource_id: str | None = None


@dataclass
class SlotLimitError(DomainError):
    """Fellow device has no slot available for a new profile / schedule."""

    used: int | None = None
    max: int | None = None
    slot_kind: str | None = None


@dataclass
class CloudUnreachableError(DomainError):
    """The Fellow cloud API is unreachable or returned a transport error."""

    upstream_url: str | None = None
    original: str | None = None
    is_retryable: ClassVar[bool] = True


@dataclass
class AuthFailedError(DomainError):
    """Fellow cloud rejected our credentials."""

    reason: str | None = None


@dataclass
class UnknownError(DomainError):
    """Catch-all for unexpected errors. Wrap unknown exceptions here."""

    original: str | None = None
