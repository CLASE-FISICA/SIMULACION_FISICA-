"""Conversión de unidades de potencia y longitud a kW y metros."""

from enum import StrEnum

from app.domain.normativa import BTU_H_POR_KW, MJ_H_POR_KW


class UnidadPotencia(StrEnum):
    KW = "kW"
    BTU_H = "BTU/h"
    MJ_H = "MJ/h"


class UnidadLongitud(StrEnum):
    M = "m"
    CM = "cm"
    MM = "mm"


_DIVISOR_POTENCIA: dict[UnidadPotencia, float] = {
    UnidadPotencia.KW: 1.0,
    UnidadPotencia.BTU_H: BTU_H_POR_KW,
    UnidadPotencia.MJ_H: MJ_H_POR_KW,
}

_DIVISOR_LONGITUD: dict[UnidadLongitud, float] = {
    UnidadLongitud.M: 1.0,
    UnidadLongitud.CM: 100.0,
    UnidadLongitud.MM: 1000.0,
}


def a_kw(valor: float, unidad: UnidadPotencia) -> float:
    """Convierte una potencia a kW (BTU/h ÷ 3412,142; MJ/h ÷ 3,6)."""
    return valor / _DIVISOR_POTENCIA[unidad]


def a_metros(valor: float, unidad: UnidadLongitud) -> float:
    """Convierte una longitud a metros (cm ÷ 100; mm ÷ 1000)."""
    return valor / _DIVISOR_LONGITUD[unidad]


def divisor_potencia(unidad: UnidadPotencia) -> float:
    return _DIVISOR_POTENCIA[unidad]


def divisor_longitud(unidad: UnidadLongitud) -> float:
    return _DIVISOR_LONGITUD[unidad]


def cm_a_pulgadas(valor_cm: float) -> float:
    return valor_cm / 2.54


def pulgadas_a_cm(valor_pulg: float) -> float:
    return valor_pulg * 2.54
