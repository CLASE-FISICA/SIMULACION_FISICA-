"""Contenido del módulo de aprendizaje.

Transcripción propia con cita del numeral, nunca el texto íntegro de la NTC 3631 (riesgo
de derechos de autor, tarea SE12). El contenido definitivo lo entrega Documentación (DO03);
esto es una semilla mínima para que el frontend tenga qué mostrar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TipoBloque = Literal["texto", "imagen", "nota", "definicion", "tabla"]


@dataclass(frozen=True)
class Bloque:
    tipo: TipoBloque
    contenido: str | None = None
    url: str | None = None
    alt: str | None = None


@dataclass(frozen=True)
class Pagina:
    slug: str
    titulo: str
    numerales: tuple[str, ...] = field(default_factory=tuple)
    bloques: tuple[Bloque, ...] = field(default_factory=tuple)


PAGINAS: dict[str, Pagina] = {
    "generalidades": Pagina(
        slug="generalidades",
        titulo="Generalidades",
        numerales=("4.1", "4.2"),
        bloques=(
            Bloque(
                tipo="texto",
                contenido=(
                    "Todo artefacto a gas debe instalarse en un recinto con ventilación "
                    "suficiente para la potencia instalada. Sin aire, la combustión es "
                    "incompleta y se produce monóxido de carbono."
                ),
            ),
            Bloque(
                tipo="definicion",
                contenido="Aire de combustión: el necesario para la combustión completa.",
            ),
            Bloque(
                tipo="definicion",
                contenido="Aire de dilución: el que se mezcla con los productos de combustión.",
            ),
            Bloque(
                tipo="definicion",
                contenido="Aire de renovación: el que repone el consumido por la combustión.",
            ),
            Bloque(
                tipo="nota",
                contenido=(
                    "El color de la llama es orientativo. No prueba la ausencia de monóxido "
                    "de carbono: eso exige medición."
                ),
            ),
        ),
    ),
    "metodo-estandar": Pagina(
        slug="metodo-estandar",
        titulo="Método estándar (numeral 4.1.1)",
        numerales=("4.1.1",),
        bloques=(
            Bloque(
                tipo="texto",
                contenido=(
                    "El volumen del recinto debe ser de al menos 3,4 m³ por cada kilovatio de "
                    "potencia nominal agregada de los artefactos de circuito abierto."
                ),
            ),
            Bloque(
                tipo="nota",
                contenido=(
                    "Los artefactos de circuito estanco (Tipo C) no se suman a la potencia: "
                    "no toman aire del recinto."
                ),
            ),
        ),
    ),
    "anexo-d": Pagina(
        slug="anexo-d",
        titulo="Anexo D — recintos a menos de 260 msnm",
        numerales=("Anexo D.1.1", "Anexo D.1.2"),
        bloques=(
            Bloque(
                tipo="texto",
                contenido=(
                    "Para recintos situados a menos de 260 msnm, la abertura debe tener un "
                    "área libre de 150 cm² por kilovatio y situarse a más de 1 m del piso."
                ),
            ),
            Bloque(
                tipo="texto",
                contenido=(
                    "El anexo admite como alternativa considerar el área libre efectiva de "
                    "puertas y ventanas que comuniquen con el exterior."
                ),
            ),
        ),
    ),
}
