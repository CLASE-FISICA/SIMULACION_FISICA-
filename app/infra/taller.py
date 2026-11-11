"""Ejercicios del taller y su corrección.

Solo el ejercicio 1 del libro está resuelto; los otros dos los resuelve Documentación
(DO04) y se validan con el instructor. Mientras tanto no se corrigen: devolver un
"correcto" inventado sería peor que decir que aún no está disponible.
"""

from __future__ import annotations

import uuid

from app.api.dto import RespuestaAprendizDTO

NAMESPACE = uuid.UUID("6f1c2a4e-8b3d-4f5a-9c7e-2d1b0a9f8e7d")


def _id(nombre: str) -> str:
    return str(uuid.uuid5(NAMESPACE, nombre))


class Ejercicio:
    def __init__(
        self,
        nombre: str,
        enunciado: str,
        esperado: RespuestaAprendizDTO | None,
        tolerancia_relativa: float = 0.02,
    ) -> None:
        self.id = _id(nombre)
        self.nombre = nombre
        self.enunciado = enunciado
        self.esperado = esperado
        self.tolerancia_relativa = tolerancia_relativa


EJERCICIOS: dict[str, Ejercicio] = {
    e.id: e
    for e in (
        Ejercicio(
            nombre="taller-1",
            enunciado=(
                "Estufa de 25 000 BTU/h y horno de 10 MJ/h en una cocina de 2,5 m × 4,7 m × "
                "2,2 m. Calcule la relación volumen/potencia y dictamine."
            ),
            esperado=RespuestaAprendizDTO(relacion_m3_kw=2.5583, veredicto="no_cumple"),
        ),
        Ejercicio(
            nombre="taller-2",
            enunciado=(
                "Cubierta de 8 kW y horno de 4 kW: volumen requerido, potencia máxima "
                "permitida y tamaño de las rejillas si hace falta."
            ),
            esperado=None,
        ),
        Ejercicio(
            nombre="taller-3",
            enunciado="Cubierta Challenger de cinco puestos: volumen necesario para cumplir el método estándar.",
            esperado=None,
        ),
    )
}
