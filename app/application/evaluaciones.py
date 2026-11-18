"""Casos de uso de la API.

Aquí se orquesta: se valida, se llama al motor, se mapea y se guarda. Ni el router ni
el dominio saben de este archivo.
"""

from __future__ import annotations

from app.api.dto import (
    EvaluacionGuardadaDTO,
    PaginaEvaluacionesDTO,
    ResultadoDTO,
    SolicitudEvaluacionDTO,
)
from app.api.mapping import evaluacion_a_dto
from app.application.motor_be1 import calcular as calcular_motor
from app.infra.repositorio import Filtros, RepositorioEvaluaciones
from app.infra.repositorio import NoEncontrado as NoEncontradoRepositorio


def calcular(solicitud: SolicitudEvaluacionDTO) -> ResultadoDTO:
    """Calcula sin guardar. Es el endpoint que usa el simulador mientras se escribe."""
    return calcular_motor(solicitud)


def crear(
    solicitud: SolicitudEvaluacionDTO,
    *,
    aprendiz_id: str,
    repositorio: RepositorioEvaluaciones,
    idempotency_key: str | None = None,
) -> EvaluacionGuardadaDTO:
    resultado = calcular(solicitud)
    almacenada = repositorio.crear(
        aprendiz_id=aprendiz_id,
        entradas=solicitud,
        resultado=resultado,
        idempotency_key=idempotency_key,
    )
    return evaluacion_a_dto(almacenada)


def listar(
    filtros: Filtros,
    *,
    repositorio: RepositorioEvaluaciones,
    alcance: str | None,
) -> PaginaEvaluacionesDTO:
    items, total = repositorio.listar(filtros, alcance=alcance)
    paginas = (total + filtros.size - 1) // filtros.size if filtros.size else 0
    return PaginaEvaluacionesDTO(
        items=[evaluacion_a_dto(i) for i in items],
        total=total,
        page=filtros.page,
        size=filtros.size,
        pages=paginas,
    )


__all__ = ["NoEncontradoRepositorio", "calcular", "crear", "listar"]
