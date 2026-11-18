"""Catálogos públicos de solo lectura (ADR-003, D10).

No requieren sesión: el simulador necesita las rejillas antes de que el aprendiz entre, y
el módulo de aprendizaje debe abrirse sin cuenta. No hay datos personales aquí.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.api.demo import CASOS
from app.api.dto import (
    ArtefactoDTO,
    CasoDTO,
    ConductoDTO,
    ListaCasosDTO,
    ListaConductosDTO,
    ListaParametrosDTO,
    ListaRejillasDTO,
    RecintoDTO,
    RejillaDTO,
)
from app.api.routers.normativa import parametros
from app.config import ajustes
from app.domain.modelos import Metodo
from app.infra import catalogo

router = APIRouter(prefix="/v1/catalogos", tags=["catalogos"])

Geometria = Literal["cuadrada", "rectangular", "circular"]


@router.get("/rejillas", response_model=ListaRejillasDTO, summary="Rejillas comerciales")
def rejillas(
    area_minima_cm2: float | None = Query(default=None, ge=0),
    geometria: Geometria | None = None,
) -> ListaRejillasDTO:
    items = catalogo.filtrar_rejillas(area_minima_cm2, geometria)
    return ListaRejillasDTO(
        items=[
            RejillaDTO(
                id=r.id,
                nombre=r.nombre,
                ancho_cm=r.ancho_cm,
                alto_cm=r.alto_cm,
                area_total_cm2=round(r.area_total_cm2, 2),
                area_efectiva_cm2=round(r.area_efectiva_cm2, 2),
                factor_obturacion=r.factor_obturacion,
                geometria=r.geometria,
                proveedor=r.proveedor,
            )
            for r in items
        ],
        catalogo_version=catalogo.CATALOGO_VERSION,
        provisional=ajustes.catalogo_provisional,
    )


@router.get("/conductos", response_model=ListaConductosDTO, summary="Conductos comerciales")
def conductos(area_minima_cm2: float | None = Query(default=None, ge=0)) -> ListaConductosDTO:
    items = catalogo.filtrar_conductos(area_minima_cm2)
    return ListaConductosDTO(
        items=[
            ConductoDTO(
                id=c.id,
                nombre=c.nombre,
                diametro_pulgadas=c.diametro_pulgadas,
                diametro_cm=round(c.diametro_cm, 2),
                area_cm2=round(c.area_cm2, 2),
                factor_obturacion=c.factor_obturacion,
            )
            for c in items
        ],
        catalogo_version=catalogo.CATALOGO_VERSION,
        provisional=ajustes.catalogo_provisional,
    )


@router.get("/casos", response_model=ListaCasosDTO, summary="Casos pedagógicos")
def casos() -> ListaCasosDTO:
    return ListaCasosDTO(
        items=[
            CasoDTO(
                id=caso.id,
                nombre=caso.nombre,
                recinto=RecintoDTO(**caso.recinto.model_dump(mode="json")),
                artefactos=[
                    ArtefactoDTO(**a.model_dump(mode="json")) for a in caso.artefactos
                ],
                numeral_esperado=caso.numeral_esperado,
                relacion_esperada=caso.relacion_esperada,
            )
            for caso in CASOS
        ]
    )


@router.get("/parametros", response_model=ListaParametrosDTO, summary="Parámetros normativos")
def parametros_normativos() -> ListaParametrosDTO:
    return parametros()


@router.get("/listas", summary="Listas de selección del libro")
def listas() -> dict[str, list[str]]:
    return {
        "tipo_recinto": [
            "cocina",
            "dormitorio",
            "bano",
            "monoespacial",
            "comercial",
            "industrial",
            "otro",
        ],
        "nivel": ["sobre_primer_sotano", "primer_sotano", "bajo_primer_sotano"],
        "metodo": [metodo.value for metodo in Metodo],
        "tipo_ventilacion": [
            "todo_el_aire_del_interior",
            "todo_el_aire_del_exterior",
            "combinacion",
            "suministro_mecanico",
        ],
        "tipo_construccion": [
            "dos_aberturas_interiores",
            "abertura_entre_pisos",
            "dos_aberturas",
            "conducto_vertical",
            "conducto_horizontal",
            "una_abertura",
            "suministro_mecanico",
        ],
    }
