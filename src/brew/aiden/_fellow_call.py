"""Wraps a sync Fellow library call as an async, error-classified coroutine.

Centralizes the try/except + asyncio.to_thread pattern so each client method
stays one line.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass

from brew.errors import CloudUnreachableError, NotFoundError

logger = logging.getLogger(__name__)

_NOT_FOUND_MARKERS = ("not found",)


@dataclass(frozen=True, slots=True)
class NotFoundSpec:
    """Identifies the resource a Fellow call is targeting, for 404 mapping."""

    resource_kind: str
    resource_id: str


def is_not_found(exc: Exception) -> bool:
    """Pattern-match Fellow library errors that look like 404s.

    Fragile by necessity — Fellow has no typed exceptions. Centralizing the
    pattern means a Fellow wording change requires editing one place, not 4.
    """
    msg = str(exc).lower()
    return any(marker in msg for marker in _NOT_FOUND_MARKERS)


async def fellow_call[T](op: str, fn: Callable[..., T], /, *args: object, **kwargs: object) -> T:
    """Run a sync Fellow call in a thread; map failures to CloudUnreachableError."""
    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    except Exception as e:
        logger.debug("Fellow %s failed", op, exc_info=True)
        raise CloudUnreachableError(
            message=f"Could not reach Fellow cloud to {op}",
            original=type(e).__name__,
        ) from e


async def fellow_call_or_not_found[T](
    op: str,
    not_found: NotFoundSpec,
    fn: Callable[..., T],
    /,
    *args: object,
    **kwargs: object,
) -> T:
    """Same as fellow_call, but if the underlying error pattern-matches a 404
    raise NotFoundError instead of CloudUnreachableError.
    """
    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    except Exception as e:
        if is_not_found(e):
            raise NotFoundError.for_resource(not_found.resource_kind, not_found.resource_id) from e
        logger.debug("Fellow %s failed", op, exc_info=True)
        raise CloudUnreachableError(
            message=f"Could not reach Fellow cloud to {op}",
            original=type(e).__name__,
        ) from e
