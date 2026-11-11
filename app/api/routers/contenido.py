"""Módulo de aprendizaje: contenido transcrito con cita de numeral."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dto import BloqueDTO, PaginaDTO
from app.api.errors import Problema
from app.infra.contenido import PAGINAS

router = APIRouter(prefix="/v1/contenido", tags=["contenido"])


@router.get("/{slug}", response_model=PaginaDTO, summary="Página del módulo de aprendizaje")
def obtener(slug: str) -> PaginaDTO:
    pagina = PAGINAS.get(slug)
    if pagina is None:
        raise Problema(
            status=404,
            code="no_encontrado",
            title="El recurso no existe",
            detail=f"No hay contenido publicado con el identificador '{slug}'.",
        )
    return PaginaDTO(
        slug=pagina.slug,
        titulo=pagina.titulo,
        numerales=list(pagina.numerales),
        bloques=[
            BloqueDTO(tipo=b.tipo, contenido=b.contenido, url=b.url, alt=b.alt)
            for b in pagina.bloques
        ],
    )
