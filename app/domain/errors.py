"""Errores del dominio. No conocen HTTP: la capa api los traduce."""

from __future__ import annotations


class ErrorDeDominio(Exception):
    """Base de los errores que el motor puede devolver."""

    codigo = "error_de_dominio"


class SinArtefactos(ErrorDeDominio):
    """No se puede evaluar un recinto sin artefactos: no hay demanda de aire."""

    codigo = "sin_artefactos"


class DatosInsuficientes(ErrorDeDominio):
    """Falta un dato que la norma exige para el método solicitado."""

    codigo = "datos_insuficientes"
