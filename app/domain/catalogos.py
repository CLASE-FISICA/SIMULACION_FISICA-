"""Catálogos provisionales y selección del elemento comercial que cumple.

El catálogo oficial lo carga Base de datos (BD-06) y la API lo pasa al motor;
estos valores por defecto solo reproducen el Excel mientras el instructor
decide cuál de sus dos catálogos es el oficial.
"""

import math
from collections.abc import Iterable

from app.domain.modelos import Conducto, Rejilla, Ventilador
from app.domain.normativa import DIMENSION_MINIMA_ABERTURA

_TOLERANCIA = 1e-9

REJILLAS_PROVISIONALES: tuple[Rejilla, ...] = (
    Rejilla(codigo="R-15x15", ancho_cm=15, alto_cm=15, origen="Simulación matemática!C23"),
    Rejilla(codigo="R-20x20", ancho_cm=20, alto_cm=20, origen="Simulación matemática!C24"),
    Rejilla(codigo="R-25x25", ancho_cm=25, alto_cm=25, origen="Simulación matemática!C25"),
    Rejilla(codigo="R-30x30", ancho_cm=30, alto_cm=30, origen="Simulación matemática!C26"),
    Rejilla(codigo="R-35x35", ancho_cm=35, alto_cm=35, origen="Simulación matemática!M33"),
    Rejilla(codigo="R-10x90", ancho_cm=10, alto_cm=90, origen="4.2.1 Método 1!I409"),
    Rejilla(codigo="R-25x80", ancho_cm=25, alto_cm=80, origen="4.2.1 Método 1!I406"),
    Rejilla(codigo="R-90x60", ancho_cm=90, alto_cm=60, origen="Simulación matemática!K64"),
)
"""Unión de los catálogos de «Simulación matemática» y «4.2.1 Método 1», más las
rejillas que el Excel escribe a mano en los casos 1 (35x35) y 7 (90x60)."""

CONDUCTOS_PROVISIONALES: tuple[Conducto, ...] = tuple(
    Conducto(diametro_pulg=d) for d in range(3, 11)
)
"""Conductos circulares comerciales de 3 a 10 pulgadas (BD-06)."""

VENTILADORES_PROVISIONALES: tuple[Ventilador, ...] = tuple(
    Ventilador(capacidad_m3h=c, origen="Provisional; el Excel usa 100 m³/h en J69")
    for c in (100, 150, 200, 300, 400, 500, 800, 1000, 1500, 2000, 3000)
)


def seleccionar_rejilla(
    area_libre_cm2: float,
    factor_rejilla: float,
    catalogo: Iterable[Rejilla] = REJILLAS_PROVISIONALES,
) -> Rejilla | None:
    """La rejilla de menor área total cuya área efectiva cubre el área libre.

    Se descartan las rejillas con un lado menor que la dimensión mínima de
    8 cm. A igual área, gana la más cuadrada. None si ninguna alcanza.
    """
    candidatas = [
        r for r in catalogo
        if r.area_efectiva_cm2(factor_rejilla) + _TOLERANCIA >= area_libre_cm2
        and min(r.ancho_cm, r.alto_cm) >= DIMENSION_MINIMA_ABERTURA.valor
    ]
    if not candidatas:
        return None
    return min(candidatas, key=lambda r: (r.area_total_cm2, abs(r.ancho_cm - r.alto_cm)))


def seleccionar_conducto(
    seccion_cm2: float,
    catalogo: Iterable[Conducto] = CONDUCTOS_PROVISIONALES,
) -> Conducto | None:
    """El conducto circular de menor diámetro cuya sección cubre la requerida."""
    candidatos = [c for c in catalogo if c.area_cm2 + _TOLERANCIA >= seccion_cm2]
    return min(candidatos, key=lambda c: c.diametro_pulg) if candidatos else None


def seleccionar_ventilador(
    caudal_m3h: float,
    catalogo: Iterable[Ventilador] = VENTILADORES_PROVISIONALES,
) -> Ventilador | None:
    candidatos = [v for v in catalogo if v.capacidad_m3h + _TOLERANCIA >= caudal_m3h]
    return min(candidatos, key=lambda v: v.capacidad_m3h) if candidatos else None


def redondear_a_multiplo(valor: float, paso: float) -> float:
    """Redondea hacia arriba al múltiplo de `paso` (lado construible de un conducto)."""
    return math.ceil(valor / paso - _TOLERANCIA) * paso