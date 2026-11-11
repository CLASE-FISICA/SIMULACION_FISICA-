"""Pruebas de la API: contrato, aislamiento y errores."""

from __future__ import annotations

import pytest
from app.api.main import app
from app.infra.repositorio import repositorio
from app.infra.taller import EJERCICIOS
from fastapi.testclient import TestClient

APRENDIZ = {"X-Dev-Usuario": "aprendiz-1", "X-Dev-Rol": "aprendiz", "X-Dev-Ficha": "ficha-1"}
OTRO_APRENDIZ = {"X-Dev-Usuario": "aprendiz-2", "X-Dev-Rol": "aprendiz", "X-Dev-Ficha": "ficha-1"}
ADMIN = {"X-Dev-Usuario": "admin", "X-Dev-Rol": "administrador"}

SOLICITUD = {
    "recinto": {"ancho_m": 1.9, "fondo_m": 1.8, "alto_m": 2.4, "tipo": "otro"},
    "artefactos": [{"nombre": "Calentador", "potencia_kw": 11.4}],
}


@pytest.fixture()
def cliente() -> TestClient:
    repositorio.vaciar()
    return TestClient(app)


# --- Estado y catálogos -----------------------------------------------------


def test_health_es_publico(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["norma_version"]


def test_normativa_expone_las_constantes_con_numeral(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/normativa")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["area_minima_abertura_cm2"] == 64.0
    assert len(cuerpo["constantes"]) >= 13
    assert all(c["numeral"] for c in cuerpo["constantes"])
    practicas = [c for c in cuerpo["constantes"] if c["estado_validacion"] == "practica_de_diseno"]
    assert practicas, "el factor de rejilla y el margen deben declararse como práctica de diseño"


def test_rejillas_declaran_area_efectiva_y_provisional(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/catalogos/rejillas")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["provisional"] is True
    for rejilla in cuerpo["items"]:
        assert rejilla["area_efectiva_cm2"] == pytest.approx(
            rejilla["area_total_cm2"] * 0.6, rel=1e-3
        )
    areas = [r["area_efectiva_cm2"] for r in cuerpo["items"]]
    assert areas == sorted(areas), "el catálogo debe venir ordenado por área efectiva"


def test_rejillas_filtradas_por_area(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/catalogos/rejillas", params={"area_minima_cm2": 645})
    areas = [r["area_efectiva_cm2"] for r in respuesta.json()["items"]]
    assert areas and min(areas) >= 645


def test_conductos_comerciales(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/catalogos/conductos")
    items = respuesta.json()["items"]
    assert [c["diametro_pulgadas"] for c in items] == sorted(c["diametro_pulgadas"] for c in items)
    seis = next(c for c in items if c["diametro_pulgadas"] == 6)
    assert seis["area_cm2"] == pytest.approx(182.4, abs=0.1)


def test_casos_precargados(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/catalogos/casos")
    assert respuesta.status_code == 200
    casos = respuesta.json()["items"]
    assert len(casos) == 8
    assert casos[0]["relacion_esperada"] == pytest.approx(0.72)


def test_listas_del_libro(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/catalogos/listas")
    assert respuesta.status_code == 200
    assert "tipo_recinto" in respuesta.json()


# --- Previsualización -------------------------------------------------------


def test_preview_caso_1(cliente: TestClient) -> None:
    respuesta = cliente.post("/v1/evaluaciones/preview", json=SOLICITUD, headers=APRENDIZ)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["veredicto"] == "no_cumple"
    assert cuerpo["relacion_m3_kw"] == pytest.approx(0.72)
    assert cuerpo["numeral"] == "4.1.1"
    assert cuerpo["pasos"]
    assert cuerpo["requerimientos"] == []
    assert cuerpo["norma_version"]
    assert cuerpo["motor_version"]


def test_preview_sin_sesion_da_401_con_problem_json(cliente: TestClient) -> None:
    respuesta = cliente.post("/v1/evaluaciones/preview", json=SOLICITUD)
    assert respuesta.status_code == 401
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    assert respuesta.json()["code"] == "no_autenticado"


def test_entrada_invalida_da_422_con_detalle_de_campo(cliente: TestClient) -> None:
    cuerpo = dict(SOLICITUD)
    cuerpo["recinto"] = {"ancho_m": 3, "fondo_m": 3, "alto_m": 0}
    respuesta = cliente.post("/v1/evaluaciones/preview", json=cuerpo, headers=APRENDIZ)
    assert respuesta.status_code == 422
    problema = respuesta.json()
    assert problema["code"] == "validacion"
    assert any(e["campo"].endswith("alto_m") for e in problema["errors"])


def test_tipo_de_recinto_invalido_da_422(cliente: TestClient) -> None:
    cuerpo = dict(SOLICITUD)
    cuerpo["recinto"] = {"ancho_m": 3, "fondo_m": 3, "alto_m": 2.5, "tipo": "garaje"}
    respuesta = cliente.post("/v1/evaluaciones/preview", json=cuerpo, headers=APRENDIZ)
    assert respuesta.status_code == 422


def test_dormitorio_con_circuito_abierto_no_se_permite(cliente: TestClient) -> None:
    cuerpo = {
        "recinto": {"ancho_m": 4, "fondo_m": 4, "alto_m": 2.5, "tipo": "dormitorio"},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 7}],
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=cuerpo, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert respuesta.json()["veredicto"] == "no_permitido"


# --- Expediente -------------------------------------------------------------


def test_crear_guarda_y_devuelve_location(cliente: TestClient) -> None:
    respuesta = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ)
    assert respuesta.status_code == 201
    assert respuesta.headers["location"].startswith("/v1/evaluaciones/")
    cuerpo = respuesta.json()
    assert cuerpo["aprendiz_id"] == "aprendiz-1"
    assert cuerpo["entradas"]["artefactos"][0]["nombre"] == "Calentador"


def test_idempotency_key_no_duplica(cliente: TestClient) -> None:
    cabeceras = dict(APRENDIZ, **{"Idempotency-Key": "clave-1"})
    primera = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras)
    segunda = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras)
    assert primera.json()["id"] == segunda.json()["id"]


def test_el_aprendiz_solo_ve_lo_suyo(cliente: TestClient) -> None:
    cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ)
    cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=OTRO_APRENDIZ)

    propio = cliente.get("/v1/evaluaciones", headers=APRENDIZ).json()
    assert propio["total"] == 1

    todos = cliente.get("/v1/evaluaciones", headers=ADMIN).json()
    assert todos["total"] == 2


def test_no_puede_leer_la_evaluacion_de_otro(cliente: TestClient) -> None:
    creada = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ).json()
    respuesta = cliente.get(f"/v1/evaluaciones/{creada['id']}", headers=OTRO_APRENDIZ)
    assert respuesta.status_code == 404, "se responde no encontrado para no filtrar existencia"


def test_paginacion_con_sobre_fijo(cliente: TestClient) -> None:
    for _ in range(3):
        cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ)
    cuerpo = cliente.get("/v1/evaluaciones", params={"size": 2}, headers=ADMIN).json()
    assert cuerpo["total"] == 3
    assert cuerpo["pages"] == 2
    assert len(cuerpo["items"]) == 2
    assert {"items", "total", "page", "size", "pages"} <= set(cuerpo)


def test_eliminar(cliente: TestClient) -> None:
    creada = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ).json()
    borrado = cliente.delete(f"/v1/evaluaciones/{creada['id']}", headers=ADMIN)
    assert borrado.status_code == 204
    assert cliente.get(f"/v1/evaluaciones/{creada['id']}", headers=ADMIN).status_code == 404


def test_reporte_pdf_declara_no_implementado(cliente: TestClient) -> None:
    creada = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ).json()
    respuesta = cliente.get(f"/v1/evaluaciones/{creada['id']}/reporte.pdf", headers=APRENDIZ)
    assert respuesta.status_code == 501
    assert respuesta.json()["code"] == "regla_no_implementada"


# --- Contenido y taller -----------------------------------------------------


def test_contenido_publico(cliente: TestClient) -> None:
    respuesta = cliente.get("/v1/contenido/generalidades")
    assert respuesta.status_code == 200
    assert respuesta.json()["numerales"]


def test_contenido_inexistente_da_404(cliente: TestClient) -> None:
    assert cliente.get("/v1/contenido/no-existe").status_code == 404


def test_taller_corrige_el_ejercicio_resuelto(cliente: TestClient) -> None:
    ejercicio = next(e for e in EJERCICIOS.values() if e.nombre == "taller-1")
    respuesta = cliente.post(
        f"/v1/taller/{ejercicio.id}/intentos",
        json={"respuesta": {"relacion_m3_kw": 2.556, "veredicto": "no_cumple"}},
        headers=APRENDIZ,
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["correcto"] is True


def test_taller_rechaza_una_respuesta_equivocada(cliente: TestClient) -> None:
    ejercicio = next(e for e in EJERCICIOS.values() if e.nombre == "taller-1")
    respuesta = cliente.post(
        f"/v1/taller/{ejercicio.id}/intentos",
        json={"respuesta": {"relacion_m3_kw": 1.2, "veredicto": "cumple"}},
        headers=APRENDIZ,
    )
    assert respuesta.json()["correcto"] is False


def test_taller_no_corrige_lo_que_no_esta_resuelto(cliente: TestClient) -> None:
    ejercicio = next(e for e in EJERCICIOS.values() if e.nombre == "taller-2")
    respuesta = cliente.post(
        f"/v1/taller/{ejercicio.id}/intentos",
        json={"respuesta": {"relacion_m3_kw": 1.0}},
        headers=APRENDIZ,
    )
    assert respuesta.status_code == 409
