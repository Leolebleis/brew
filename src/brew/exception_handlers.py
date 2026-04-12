"""FastAPI exception handler mapping DomainError -> HTTP responses.

Single source of truth for DomainError -> HTTP status mapping.
Register on the FastAPI app once in main.py.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from brew.errors import (
    AuthFailedError,
    CloudUnreachableError,
    DomainError,
    NotFoundError,
    SlotLimitError,
    UnknownError,
    ValidationError,
)
from brew.response_models import ErrorResponse

logger = logging.getLogger(__name__)

_SERVER_ERROR_THRESHOLD = 500

_STATUS_MAP: dict[type[DomainError], int] = {
    ValidationError: 400,
    NotFoundError: 404,
    SlotLimitError: 409,
    CloudUnreachableError: 503,
    AuthFailedError: 502,
    UnknownError: 500,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register the DomainError handler on the FastAPI app."""

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        status = _STATUS_MAP.get(type(exc), 500)
        body = ErrorResponse.from_domain_error(exc)
        if status >= _SERVER_ERROR_THRESHOLD:
            logger.exception("DomainError returning %s", status, exc_info=exc)
        else:
            logger.info("DomainError returning %s: %s", status, body.model_dump())
        return JSONResponse(status_code=status, content={"error": body.model_dump()})
