"""Casos pedagógicos del libro, como datos de demostración.

En la versión final viven en la base de datos (tarea BD07). Aquí permiten que el
frontend y las pruebas usen los mismos datos sin escribir nada a mano.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import Artefacto, Nivel, Recinto, TipoRecinto


@dataclass(frozen=True)
class CasoDemo:
    """Un caso del libro con su resultado esperado, para cargar de un clic."""

    id: int
    nombre: str
    recinto: Recinto
    artefactos: tuple[Artefacto, ...]
    numeral_esperado: str
    relacion_esperada: float


@dataclass(frozen=True)
class EjemploPractico:
    """Un ejercicio del taller con su respuesta esperada."""

    nombre: str
    recinto: Recinto
    artefactos: tuple[Artefacto, ...]
    relacion_esperada: float


def _r(ancho: float, fondo: float, alto: float, tipo: TipoRecinto, **kw: float) -> Recinto:
    return Recinto(ancho_m=ancho, fondo_m=fondo, alto_m=alto, tipo=tipo, **kw)


CASOS: tuple[CasoDemo, ...] = (
    CasoDemo(
        id=1,
        nombre="Calentador en recinto pequeño",
        recinto=_r(1.9, 1.8, 2.4, TipoRecinto.OTRO),
        artefactos=(Artefacto(nombre="Calentador", potencia_kw=11.4),),
        numeral_esperado="4.1.2 a)",
        relacion_esperada=0.72,
    ),
    CasoDemo(
        id=2,
        nombre="Cocina con espacios comunicados en otro piso",
        recinto=_r(3.5, 4.0, 2.3, TipoRecinto.COCINA),
        artefactos=(Artefacto(nombre="Cocina", potencia_kw=9.6),),
        numeral_esperado="4.1.2 b)",
        relacion_esperada=3.3542,
    ),
    CasoDemo(
        id=3,
        nombre="Cocina y calentador con dos aberturas",
        recinto=_r(3.0, 6.0, 2.4, TipoRecinto.COCINA),
        artefactos=(
            Artefacto(nombre="Cocina", potencia_kw=9.6),
            Artefacto(nombre="Calentador", potencia_kw=11.4),
        ),
        numeral_esperado="4.2.1 a)",
        relacion_esperada=2.0571,
    ),
    CasoDemo(
        id=4,
        nombre="Conducto vertical",
        recinto=_r(5.0, 6.0, 2.4, TipoRecinto.COCINA),
        artefactos=(Artefacto(nombre="Artefacto", potencia_kw=24.0),),
        numeral_esperado="4.2.1 a)",
        relacion_esperada=3.0,
    ),
    CasoDemo(
        id=5,
        nombre="Conducto horizontal",
        recinto=_r(5.0, 6.0, 2.4, TipoRecinto.COCINA),
        artefactos=(Artefacto(nombre="Artefacto", potencia_kw=24.0),),
        numeral_esperado="4.2.1 b)",
        relacion_esperada=3.0,
    ),
    CasoDemo(
        id=6,
        nombre="Una sola abertura",
        recinto=_r(3.0, 6.0, 2.4, TipoRecinto.COCINA),
        artefactos=(
            Artefacto(nombre="Cocina", potencia_kw=9.6),
            Artefacto(nombre="Calentador", potencia_kw=11.4),
        ),
        numeral_esperado="4.2.2",
        relacion_esperada=2.0571,
    ),
    CasoDemo(
        id=7,
        nombre="Recinto a menos de 260 msnm",
        recinto=_r(3.0, 6.0, 2.4, TipoRecinto.COCINA, altitud_msnm=100.0),
        artefactos=(
            Artefacto(nombre="Cocina", potencia_kw=9.6),
            Artefacto(nombre="Calentador", potencia_kw=11.4),
        ),
        numeral_esperado="Anexo D",
        relacion_esperada=2.0571,
    ),
    CasoDemo(
        id=8,
        nombre="Suministro mecánico en restaurante",
        recinto=Recinto(
            ancho_m=6.0,
            fondo_m=6.0,
            alto_m=3.0,
            tipo=TipoRecinto.COMERCIAL,
            nivel=Nivel.SOBRE_PRIMER_SOTANO,
        ),
        artefactos=(
            Artefacto(nombre="Estufa industrial", potencia_kw=15.0),
            Artefacto(nombre="Horno industrial", potencia_kw=12.0),
            Artefacto(nombre="Freidora", potencia_kw=10.0),
        ),
        numeral_esperado="4.4",
        relacion_esperada=2.9189,
    ),
)

TALLER = EjemploPractico(
    nombre="Taller práctico, ejercicio 1",
    recinto=_r(2.5, 4.7, 2.2, TipoRecinto.COCINA),
    artefactos=(
        Artefacto(nombre="Estufa 25 000 BTU/h", potencia_kw=25000 / 3412.142),
        Artefacto(nombre="Horno 10 MJ/h", potencia_kw=10 / 3.6),
    ),
    relacion_esperada=2.5583,
)
