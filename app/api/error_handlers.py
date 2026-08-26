"""Map domain exceptions onto consistent JSON error responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    ConfigurationError,
    ExportError,
    OpportunityEngineError,
    RecordValidationError,
    RepositoryError,
    SourceError,
)
from app.schemas.api import ErrorBody, ErrorResponse


def _error(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or {}))
    return JSONResponse(status_code=status, content=body.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RecordValidationError)
    async def _validation(_request: Request, exc: RecordValidationError) -> JSONResponse:
        return _error(422, "validation_error", exc.message, exc.details)

    @app.exception_handler(ConfigurationError)
    async def _config(_request: Request, exc: ConfigurationError) -> JSONResponse:
        return _error(400, "configuration_error", exc.message, exc.details)

    @app.exception_handler(SourceError)
    async def _source(_request: Request, exc: SourceError) -> JSONResponse:
        return _error(502, "source_error", exc.message, exc.details)

    @app.exception_handler(ExportError)
    async def _export(_request: Request, exc: ExportError) -> JSONResponse:
        return _error(500, "export_error", exc.message, exc.details)

    @app.exception_handler(RepositoryError)
    async def _repo(_request: Request, exc: RepositoryError) -> JSONResponse:
        return _error(500, "repository_error", exc.message, exc.details)

    @app.exception_handler(OpportunityEngineError)
    async def _domain(_request: Request, exc: OpportunityEngineError) -> JSONResponse:
        return _error(400, "application_error", exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _pydantic(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(
            422, "request_validation_error", "Request failed validation", {"errors": exc.errors()}
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error(exc.status_code, "http_error", str(exc.detail))
