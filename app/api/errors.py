"""Modelo de errores de la API: RFC 9457 más un código propio del dominio.

Decisión D3 del ADR-003. Todo error, en cualquier endpoint, sale con
`Content-Type: application/problem+json` y la misma forma.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

BASE_PROBLEMAS = "https://simulador-ntc3631.example/problemas"


class Problema(Exception):
    """Error de la capa API con su código estable."""

    def __init__(
        self,
        *,
        status: int,
        code: str,
        title: str,
        detail: str,
        instance: str | None = None,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.instance = instance
        self.errors = errors


def cuerpo(
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    instance: str | None = None,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Construye el documento de problema. Una sola forma para toda la API."""
    documento: dict[str, Any] = {
        "type": f"{BASE_PROBLEMAS}/{code}",
        "title": title,
        "status": status,
        "detail": detail,
    }
    if instance:
        documento["instance"] = instance
    documento["code"] = code
    if errors:
        documento["errors"] = errors
    return documento


def _respuesta(documento: dict[str, Any], status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=documento,
        media_type="application/problem+json",
    )


async def _manejar_problema(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, Problema)
    return _respuesta(
        cuerpo(
            status=exc.status,
            code=exc.code,
            title=exc.title,
            detail=exc.detail,
            instance=exc.instance,
            errors=exc.errors,
        ),
        exc.status,
    )


async def _manejar_validacion(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errores = []
    for error in exc.errors():
        campo = ".".join(str(p) for p in error["loc"] if p not in ("body", "query", "path"))
        errores.append({"campo": campo or "cuerpo", "mensaje": error["msg"]})
    return _respuesta(
        cuerpo(
            status=422,
            code="validacion",
            title="Entrada inválida",
            detail="Uno o más campos no cumplen las reglas del contrato.",
            errors=errores,
        ),
        422,
    )


async def _manejar_http(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    codigos = {
        401: ("no_autenticado", "Falta la sesión"),
        403: ("sin_permiso", "La sesión no tiene permiso sobre este recurso"),
        404: ("no_encontrado", "El recurso no existe"),
        405: ("metodo_no_permitido", "Método no permitido"),
        409: ("conflicto", "Conflicto con el estado actual del recurso"),
    }
    code, title = codigos.get(exc.status_code, ("error", "Error"))
    return _respuesta(
        cuerpo(
            status=exc.status_code,
            code=code,
            title=title,
            detail=str(exc.detail),
            instance=str(request.url.path),
        ),
        exc.status_code,
    )


async def _manejar_inesperado(request: Request, exc: Exception) -> JSONResponse:
    return _respuesta(
        cuerpo(
            status=500,
            code="error_interno",
            title="Error interno",
            detail="El servicio no pudo completar la operación.",
            instance=str(request.url.path),
        ),
        500,
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(Problema, _manejar_problema)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(Exception, _manejar_inesperado)
