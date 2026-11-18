"""Estado del servicio. Sin autenticación."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api.dto import EstadoDTO
from app.config import ajustes
from app.domain.normativa import VERSION_MOTOR

router = APIRouter(tags=["estado"])


@router.get("/health", response_model=EstadoDTO, summary="Estado del servicio")
def health() -> EstadoDTO:
    return EstadoDTO(
        estado="ok",
        version=__version__,
        motor_version=VERSION_MOTOR,
        norma_version=ajustes.norma_version,
    )
