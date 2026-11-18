"""Suite de regresión: los 8 casos del libro y el taller.

Estos valores salen de recalcular el Excel a mano. Si alguno cambia, el motor dejó de
reproducir el material del instructor y hay que detenerse.
"""

from __future__ import annotations

import pytest
from app.api.demo import CASOS, TALLER, CasoDemo
from app.api.main import app
from app.domain.engine import evaluar
from app.domain.models import Veredicto
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("caso", "relacion", "volumen"),
    [
        (1, 0.72, 8.208),
        (2, 3.3542, 32.2),
        (3, 2.0571, 43.2),
        (4, 3.0, 72.0),
        (5, 3.0, 72.0),
        (6, 2.0571, 43.2),
        (7, 2.0571, 43.2),
        (8, 2.9189, 108.0),
    ],
    ids=[f"caso-{i}" for i in range(1, 9)],
)
def test_relacion_volumen_potencia(caso: int, relacion: float, volumen: float) -> None:
    datos = next(c for c in CASOS if c.id == caso)
    resultado = evaluar(datos.recinto, list(datos.artefactos))

    assert resultado.volumen_m3 == pytest.approx(volumen, abs=0.001)
    assert resultado.relacion_m3_kw == pytest.approx(relacion, abs=0.001)


@pytest.mark.parametrize("caso", range(1, 9), ids=[f"caso-{i}" for i in range(1, 9)])
def test_ningun_caso_cumple_el_metodo_estandar(caso: int) -> None:
    """Los 8 casos del libro están deliberadamente por debajo de 3,4 m³/kW."""
    datos = next(c for c in CASOS if c.id == caso)
    resultado = evaluar(datos.recinto, list(datos.artefactos))

    assert resultado.veredicto is Veredicto.NO_CUMPLE
    assert resultado.numeral == "4.1.1"
    assert resultado.volumen_requerido_m3 > resultado.volumen_efectivo_m3


def test_todos_los_casos_traen_su_numeral_y_su_resultado() -> None:
    """Un caso sin numeral de referencia no sirve como prueba de regresión."""
    for caso in CASOS:
        assert caso.numeral_esperado
        assert caso.relacion_esperada > 0


def test_taller_ejercicio_1() -> None:
    """Estufa de 25 000 BTU/h y horno de 10 MJ/h en 2,5 × 4,7 × 2,2 m."""
    resultado = evaluar(TALLER.recinto, list(TALLER.artefactos))

    assert resultado.potencia_agregada_kw == pytest.approx(10.1046, abs=0.001)
    assert resultado.volumen_m3 == pytest.approx(25.85, abs=0.001)
    assert resultado.relacion_m3_kw == pytest.approx(TALLER.relacion_esperada, abs=0.001)
    assert resultado.veredicto is Veredicto.NO_CUMPLE


@pytest.mark.parametrize("caso", CASOS, ids=[f"caso-{c.id}" for c in CASOS])
def test_ocho_casos_del_libro_pasan_por_el_motor_be1_en_la_api(caso: CasoDemo) -> None:
    solicitud = {
        "recinto": caso.recinto.model_dump(mode="json"),
        "artefactos": [a.model_dump(mode="json") for a in caso.artefactos],
    }
    respuesta = TestClient(app).post(
        "/v1/evaluaciones/preview",
        json=solicitud,
        headers={"X-Dev-Usuario": "aprendiz-1", "X-Dev-Rol": "aprendiz"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["relacion_m3_kw"] == pytest.approx(caso.relacion_esperada, abs=0.001)
