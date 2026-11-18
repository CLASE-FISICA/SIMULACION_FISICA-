"""Catálogo de rejillas y conductos.

Los datos son PROVISIONALES: salen del libro del instructor y su unificación. El plan
exige validarlos con proveedor real antes del sprint 4 (tarea BD06). Mientras no estén
validados, la respuesta lo declara con `provisional: true` y el frontend debe mostrarlo.

El área efectiva no se escribe a mano: se calcula del área total y del factor de
obturación, para que no existan dos verdades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.catalogos import CONDUCTOS_PROVISIONALES
from app.domain.constants import FACTOR_OBTURACION_REJILLA

CATALOGO_VERSION = "2026.11-provisional"

Geometria = Literal["cuadrada", "rectangular", "circular"]


@dataclass(frozen=True)
class Rejilla:
    id: str
    nombre: str
    ancho_cm: float
    alto_cm: float
    geometria: Geometria = "cuadrada"
    proveedor: str | None = None

    @property
    def area_total_cm2(self) -> float:
        return self.ancho_cm * self.alto_cm

    @property
    def area_efectiva_cm2(self) -> float:
        return self.area_total_cm2 * FACTOR_OBTURACION_REJILLA.valor

    @property
    def factor_obturacion(self) -> float:
        return FACTOR_OBTURACION_REJILLA.valor


@dataclass(frozen=True)
class Conducto:
    id: str
    diametro_pulgadas: float
    factor_obturacion: float = 1.0

    @property
    def nombre(self) -> str:
        return f"{self.diametro_pulgadas:g} pulgadas"

    @property
    def diametro_cm(self) -> float:
        return self.diametro_pulgadas * 2.54

    @property
    def area_cm2(self) -> float:
        radio = self.diametro_cm / 2
        return 3.141592653589793 * radio * radio


# Unifica los dos catálogos del libro: los 4 tamaños de «Simulación matemática» y los
# 6 de «4.2.1 Método 1», más 35x35 y 90x60 que el propio libro recomienda y que no
# existían en ninguno de los dos.
REJILLAS: tuple[Rejilla, ...] = (
    Rejilla("R-10x10", "10x10", 10, 10),
    Rejilla("R-15x15", "15x15", 15, 15),
    Rejilla("R-20x20", "20x20", 20, 20),
    Rejilla("R-25x25", "25x25", 25, 25),
    Rejilla("R-30x30", "30x30", 30, 30),
    Rejilla("R-35x35", "35x35", 35, 35),
    Rejilla("R-10x90", "10x90", 10, 90, geometria="rectangular"),
    Rejilla("R-15x60", "15x60", 15, 60, geometria="rectangular"),
    Rejilla("R-25x80", "25x80", 25, 80, geometria="rectangular"),
    Rejilla("R-90x60", "90x60", 90, 60, geometria="rectangular"),
)

CONDUCTOS: tuple[Conducto, ...] = tuple(
    Conducto(f"C-{item.diametro_pulg}\"", float(item.diametro_pulg))
    for item in CONDUCTOS_PROVISIONALES
)


def filtrar_rejillas(
    area_minima_cm2: float | None = None,
    geometria: str | None = None,
) -> list[Rejilla]:
    items = REJILLAS
    if geometria:
        items = tuple(r for r in items if r.geometria == geometria)
    if area_minima_cm2 is not None:
        items = tuple(r for r in items if r.area_efectiva_cm2 >= area_minima_cm2)
    return sorted(items, key=lambda r: r.area_efectiva_cm2)


def filtrar_conductos(area_minima_cm2: float | None = None) -> list[Conducto]:
    items = CONDUCTOS
    if area_minima_cm2 is not None:
        items = tuple(c for c in items if c.area_cm2 >= area_minima_cm2)
    return sorted(items, key=lambda c: c.area_cm2)


def menor_rejilla_que_cumple(area_libre_requerida_cm2: float) -> Rejilla | None:
    """La más pequeña cuya área efectiva alcanza lo exigido.

    Regla del plan: la web elige del catálogo, no escribe la medida a mano. Si ninguna
    alcanza, devuelve None y el motor debe proponer varias o una medida a construir.
    """
    candidatas = [r for r in REJILLAS if r.area_efectiva_cm2 >= area_libre_requerida_cm2]
    return min(candidatas, key=lambda r: r.area_efectiva_cm2) if candidatas else None
