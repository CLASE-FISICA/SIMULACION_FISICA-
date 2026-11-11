"""Constantes normativas con su numeral.

`/v1/normativa` y `/v1/catalogos/parametros` devuelven los mismos datos a propósito: el
primero es la vista del motor (uso interno y del módulo de aprendizaje) y el segundo es la
vista pública del catálogo. Ambos leen de la misma función para que no puedan divergir.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.api.dto import ConstanteDTO, ListaParametrosDTO, NormativaDTO
from app.config import ajustes
from app.domain import constants as C

router = APIRouter(tags=["normativa"])

EstadoValidacion = Literal["validado", "pendiente_instructor", "practica_de_diseno"]

PRACTICAS = {"práctica de diseño", "recomendación del instructor"}


def constantes() -> list[ConstanteDTO]:
    salida: list[ConstanteDTO] = []
    for constante in C.NORMATIVA.values():
        estado: EstadoValidacion = (
            "practica_de_diseno" if constante.numeral in PRACTICAS else "validado"
        )
        salida.append(
            ConstanteDTO(
                clave=constante.clave,
                valor=constante.valor,
                unidad=constante.unidad,
                numeral=constante.numeral,
                descripcion=constante.descripcion,
                estado_validacion=estado,
            )
        )
    return salida


@router.get("/v1/normativa", response_model=NormativaDTO, summary="Constantes normativas")
def normativa() -> NormativaDTO:
    return NormativaDTO(
        constantes=constantes(),
        area_minima_abertura_cm2=C.area_minima_abertura_cm2(),
        norma_version=ajustes.norma_version,
        nota=(
            "Copia de solo lectura. La fuente de verdad es el motor: una prueba verifica "
            "que coinciden."
        ),
    )


def parametros() -> ListaParametrosDTO:
    return ListaParametrosDTO(items=constantes())
