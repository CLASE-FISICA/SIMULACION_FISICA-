"""Configuración del servicio, por variables de entorno. Sin secretos en el repo."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


@dataclass(frozen=True)
class Ajustes:
    """Ajustes de ejecución.

    norma_version es el valor que viaja en cada resultado y se guarda con la evaluación.
    Está pendiente de confirmar la edición con el instructor: mientras tanto se puede
    fijar por entorno sin tocar código.
    """

    dev_mode: bool = _bool("DEV_MODE", True)
    norma_version: str = os.getenv("NORMA_VERSION", "NTC 3631:2020")
    pdf_habilitado: bool = _bool("PDF_HABILITADO", False)
    catalogo_provisional: bool = _bool("CATALOGO_PROVISIONAL", True)


ajustes = Ajustes()
