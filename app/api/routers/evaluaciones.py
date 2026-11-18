"""Evaluaciones: cálculo, expediente y reporte."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.api import mapping
from app.api.dto import (
    EvaluacionGuardadaDTO,
    PaginaEvaluacionesDTO,
    ResultadoDTO,
    SolicitudEvaluacionDTO,
)
from app.api.errors import Problema
from app.api.security import UsuarioActual
from app.application import evaluaciones as caso_uso
from app.config import ajustes
from app.domain.errors import ErrorDeDominio
from app.domain.modelos import ErrorDominio as ErrorMotorBE1
from app.infra.repositorio import Filtros, NoEncontrado, repositorio

router = APIRouter(prefix="/v1/evaluaciones", tags=["evaluaciones"])


def _alcance(usuario: object) -> str | None:
    """Devuelve el id del aprendiz cuando el rol solo puede ver lo propio.

    El aislamiento no es opcional: es una prueba de seguridad (SE03).
    """
    rol = getattr(usuario, "rol", "aprendiz")
    return getattr(usuario, "id", None) if rol == "aprendiz" else None


@router.post(
    "/preview",
    response_model=ResultadoDTO,
    summary="Evalúa un recinto sin guardarlo",
)
def preview(solicitud: SolicitudEvaluacionDTO, usuario: UsuarioActual) -> ResultadoDTO:
    try:
        return caso_uso.calcular(solicitud)
    except (ErrorDeDominio, ErrorMotorBE1) as exc:
        raise Problema(
            status=422,
            code=exc.codigo if isinstance(exc, ErrorDeDominio) else "validacion",
            title="No se puede evaluar el recinto",
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=EvaluacionGuardadaDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Calcula y guarda una evaluación",
)
def crear(
    solicitud: SolicitudEvaluacionDTO,
    usuario: UsuarioActual,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> EvaluacionGuardadaDTO:
    try:
        guardada = caso_uso.crear(
            solicitud,
            aprendiz_id=usuario.id,
            repositorio=repositorio,
            idempotency_key=idempotency_key,
        )
    except (ErrorDeDominio, ErrorMotorBE1) as exc:
        raise Problema(
            status=422,
            code=exc.codigo if isinstance(exc, ErrorDeDominio) else "validacion",
            title="No se puede evaluar el recinto",
            detail=str(exc),
        ) from exc
    response.headers["Location"] = f"/v1/evaluaciones/{guardada.id}"
    return guardada


@router.get("", response_model=PaginaEvaluacionesDTO, summary="Lista evaluaciones")
def listar(
    usuario: UsuarioActual,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    ficha_id: str | None = None,
    aprendiz_id: str | None = None,
    veredicto: str | None = None,
    orden: str = Query(default="fecha_desc", pattern="^(fecha_desc|fecha_asc)$"),
) -> PaginaEvaluacionesDTO:
    filtros = Filtros(
        page=page,
        size=size,
        ficha_id=ficha_id,
        aprendiz_id=aprendiz_id,
        veredicto=veredicto,
        orden=orden,
    )
    if usuario.rol == "instructor":
        if not usuario.ficha_id or (ficha_id and ficha_id != usuario.ficha_id):
            raise Problema(
                status=403,
                code="sin_permiso",
                title="La sesión no tiene permiso sobre esta ficha",
                detail="El instructor solo puede consultar evaluaciones de su ficha asignada.",
            )
        filtros.ficha_id = usuario.ficha_id
    return caso_uso.listar(filtros, repositorio=repositorio, alcance=_alcance(usuario))


@router.get(
    "/{evaluacion_id}",
    response_model=EvaluacionGuardadaDTO,
    summary="Detalle de una evaluación",
)
def obtener(evaluacion_id: str, usuario: UsuarioActual) -> EvaluacionGuardadaDTO:
    try:
        almacenada = repositorio.obtener(evaluacion_id, aprendiz_id=_alcance(usuario))
        if usuario.rol == "instructor" and (
            not usuario.ficha_id or almacenada.ficha_id != usuario.ficha_id
        ):
            raise NoEncontrado(evaluacion_id)
    except NoEncontrado as exc:
        raise Problema(
            status=404,
            code="no_encontrado",
            title="El recurso no existe",
            detail="La evaluación no existe o no pertenece al usuario.",
        ) from exc
    return mapping.evaluacion_a_dto(almacenada)


@router.delete(
    "/{evaluacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina una evaluación",
)
def eliminar(evaluacion_id: str, usuario: UsuarioActual) -> Response:
    try:
        if usuario.rol == "instructor" and not usuario.ficha_id:
            raise NoEncontrado(evaluacion_id)
        repositorio.eliminar(
            evaluacion_id,
            aprendiz_id=_alcance(usuario),
            ficha_id=usuario.ficha_id if usuario.rol == "instructor" else None,
        )
    except NoEncontrado as exc:
        raise Problema(
            status=404,
            code="no_encontrado",
            title="El recurso no existe",
            detail="La evaluación no existe o no pertenece al usuario.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{evaluacion_id}/reporte.pdf",
    summary="Reporte en PDF con numerales y medidas",
    response_class=Response,
)
def reporte(evaluacion_id: str, usuario: UsuarioActual) -> Response:
    try:
        if usuario.rol == "instructor" and not usuario.ficha_id:
            raise NoEncontrado(evaluacion_id)
        repositorio.obtener(
            evaluacion_id,
            aprendiz_id=_alcance(usuario),
            ficha_id=usuario.ficha_id if usuario.rol == "instructor" else None,
        )
    except NoEncontrado as exc:
        raise Problema(
            status=404,
            code="no_encontrado",
            title="El recurso no existe",
            detail="La evaluación no existe o no pertenece al usuario.",
        ) from exc

    if not ajustes.pdf_habilitado:
        # La generación va por cola (ADR-003, D8) y entra en el sprint 4 (BE11).
        raise Problema(
            status=501,
            code="regla_no_implementada",
            title="Generación no habilitada",
            detail="La generación del reporte entra en el sprint 4.",
        )

    # Cuando PDF_HABILITADO esté activo, aquí se devuelve el flujo del documento
    # encolado (BE11). Mientras tanto, el 501 de arriba es la respuesta honesta.
    raise Problema(
        status=501,
        code="regla_no_implementada",
        title="Generación no habilitada",
        detail="La generación del reporte entra en el sprint 4.",
    )
