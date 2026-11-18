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
INSTRUCTOR = {"X-Dev-Usuario": "instructor-1", "X-Dev-Rol": "instructor", "X-Dev-Ficha": "ficha-1"}

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


def test_salud_y_normativa_declaran_version_del_motor_activo(cliente: TestClient) -> None:
    resultado = cliente.post("/v1/evaluaciones/preview", json=SOLICITUD, headers=APRENDIZ).json()
    assert cliente.get("/health").json()["norma_version"] == resultado["norma_version"]
    assert cliente.get("/v1/normativa").json()["norma_version"] == resultado["norma_version"]
    assert cliente.get("/health").json()["motor_version"] == resultado["motor_version"]


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


def test_preview_no_presenta_metodo_condicional_como_aplicable(cliente: TestClient) -> None:
    respuesta = cliente.post("/v1/evaluaciones/preview", json=SOLICITUD, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert not any(
        advertencia.startswith("Método propuesto por el motor:")
        for advertencia in respuesta.json()["advertencias"]
    )


def test_preview_dimensiona_metodo_exterior_de_be1(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4, "tipo": "cocina"},
        "artefactos": [
            {"nombre": "Cocina", "potencia_kw": 9.6},
            {"nombre": "Calentador", "potencia_kw": 11.4},
        ],
        "metodo": "4.2.1-directa",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["numeral"] == "4.2.1 a)"
    assert cuerpo["requerimientos"][0]["area_libre_min_cm2"] == pytest.approx(126)
    assert cuerpo["requerimientos"][0]["cantidad"] == 2


def test_metodo_exterior_no_propone_obra_para_dormitorio_prohibido(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 3, "alto_m": 2.4, "tipo": "dormitorio"},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 7}],
        "metodo": "4.2.1-directa",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert respuesta.json()["veredicto"] == "no_permitido"
    assert respuesta.json()["requerimientos"] == []


@pytest.mark.parametrize("tipo,nivel,aviso", [
    ("monoespacial", "sobre_primer_sotano", "Anexo B"),
    ("cocina", "primer_sotano", "numeral 4"),
])
def test_recintos_especiales_conservan_advertencias(
    cliente: TestClient, tipo: str, nivel: str, aviso: str,
) -> None:
    solicitud = {
        "recinto": {"ancho_m": 6, "fondo_m": 6, "alto_m": 3, "tipo": tipo, "nivel": nivel},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 7}],
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert any(aviso in texto for texto in respuesta.json()["advertencias"])


def test_anexo_d_fuera_de_altitud_no_es_ubicacion_prohibida(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 2, "fondo_m": 2, "alto_m": 2.4, "altitud_msnm": 1000},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 7}],
        "metodo": "anexo-d",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "validacion"


def test_anexo_d_rechazado_aun_con_volumen_suficiente(
    cliente: TestClient,
) -> None:
    solicitud = {
        "recinto": {"ancho_m": 6, "fondo_m": 6, "alto_m": 3, "altitud_msnm": 1000},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 7}],
        "metodo": "anexo-d",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "validacion"


def test_metodo_2_usa_diametro_y_tipo_b_del_artefacto(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 2, "fondo_m": 2, "alto_m": 2.4},
        "artefactos": [{
            "nombre": "Calentador B", "potencia_kw": 7, "tipo_artefacto": "B",
            "diametro_conector_cm": 12,
            "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
            "separacion_frontal_cm": 16,
        }],
        "metodo": "4.2.2",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert respuesta.json()["requerimientos"][0]["area_libre_min_cm2"] == pytest.approx(
        36 * 3.141592653589793
    )


def test_metodo_2_rechaza_tipo_b_sin_diametro(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4},
        "artefactos": [{"nombre": "Calentador B", "potencia_kw": 21, "tipo_artefacto": "B"}],
        "metodo": "4.2.2",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422


def test_metodo_2_rechaza_separaciones_sin_declarar(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4},
        "artefactos": [{"nombre": "Estufa A", "potencia_kw": 21}],
        "metodo": "4.2.2",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422


def test_combinacion_con_metodo_2_exige_diametro_tipo_b(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {
            "ancho_m": 3, "fondo_m": 6, "alto_m": 2.4,
            "volumen_comunicado_m3": 10,
        },
        "artefactos": [{
            "nombre": "Calentador B", "potencia_kw": 21, "tipo_artefacto": "B",
            "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
            "separacion_frontal_cm": 16,
        }],
        "metodo": "4.3",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422


def test_metodo_2_no_exige_separaciones_a_tipo_c(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4},
        "artefactos": [
            {"nombre": "Estufa A", "potencia_kw": 21,
             "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
             "separacion_frontal_cm": 16},
            {"nombre": "Estanco C", "potencia_kw": 7, "circuito": "estanco"},
        ],
        "metodo": "4.2.2",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert respuesta.json()["requerimientos"]


def test_suministro_mecanico_incluye_caudal_y_extraccion(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 21}],
        "opciones": {"extraccion_cocina_m3h": 30},
        "metodo": "4.4",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    requerimiento = respuesta.json()["requerimientos"][0]
    assert requerimiento["caudal_min_m3h"] == pytest.approx(72.84)


def test_suministro_mecanico_no_sugiere_ventilador_inferior_al_total(
    cliente: TestClient,
) -> None:
    solicitud = {
        "recinto": {"ancho_m": 3, "fondo_m": 6, "alto_m": 2.4},
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 21}],
        "opciones": {"extraccion_cocina_m3h": 4000},
        "metodo": "4.4",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["requerimientos"][0]["caudal_min_m3h"] == pytest.approx(4042.84)
    assert not any("Ventilador:" in paso["titulo"] for paso in cuerpo["pasos"])


def test_combinacion_incluye_abertura_exterior_e_interior(cliente: TestClient) -> None:
    solicitud = {
        "recinto": {
            "ancho_m": 3, "fondo_m": 6, "alto_m": 2.4, "volumen_comunicado_m3": 10
        },
        "artefactos": [{
            "nombre": "Estufa", "potencia_kw": 21,
            "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
            "separacion_frontal_cm": 16,
        }],
        "metodo": "4.3",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert len(respuesta.json()["requerimientos"]) == 2
    assert respuesta.json()["requerimientos"][1]["numeral"] == "4.1.2 a)"


@pytest.mark.parametrize("comunicado", [0, 100])
def test_combinacion_inaplicable_no_propone_abertura_exterior(
    cliente: TestClient, comunicado: float,
) -> None:
    solicitud = {
        "recinto": {
            "ancho_m": 2, "fondo_m": 2, "alto_m": 2.4,
            "volumen_comunicado_m3": comunicado,
        },
        "artefactos": [{"nombre": "Estufa", "potencia_kw": 21}],
        "metodo": "4.3",
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 422


@pytest.mark.parametrize("metodo", [
    "4.1.2a", "4.1.2b", "4.2.1-directa", "4.2.1-vertical",
    "4.2.1-horizontal", "4.2.2", "4.3", "anexo-d", "4.4",
])
def test_metodos_be1_son_accesibles_desde_preview(cliente: TestClient, metodo: str) -> None:
    solicitud = {
        "recinto": {
            "ancho_m": 3, "fondo_m": 6, "alto_m": 2.4,
            "volumen_comunicado_m3": 10 if metodo == "4.3" else 40, "altitud_msnm": 100,
        },
        "artefactos": [{
            "nombre": "Estufa", "potencia_kw": 21,
            "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
            "separacion_frontal_cm": 16,
        }],
        "metodo": metodo,
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
    assert respuesta.status_code == 200
    assert respuesta.json()["requerimientos"]


def test_catalogo_metodos_coincide_con_entradas_del_motor(cliente: TestClient) -> None:
    from app.domain.modelos import Metodo

    assert set(cliente.get("/v1/catalogos/listas").json()["metodo"]) == {
        metodo.value for metodo in Metodo
    }


def test_catalogo_publico_incluye_todos_los_conductos_del_motor(cliente: TestClient) -> None:
    from app.domain.catalogos import CONDUCTOS_PROVISIONALES

    publicados = {
        item["diametro_pulgadas"]
        for item in cliente.get("/v1/catalogos/conductos").json()["items"]
    }
    assert publicados == {item.diametro_pulg for item in CONDUCTOS_PROVISIONALES}


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


def test_tipo_b_no_puede_ser_circuito_estanco(cliente: TestClient) -> None:
    solicitud = {
        **SOLICITUD,
        "artefactos": [{
            "nombre": "Inconsistente", "potencia_kw": 7,
            "circuito": "estanco", "tipo_artefacto": "B",
        }],
    }
    respuesta = cliente.post("/v1/evaluaciones/preview", json=solicitud, headers=APRENDIZ)
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


def test_evaluacion_guardada_conserva_metodo_y_tipo_artefacto(cliente: TestClient) -> None:
    solicitud = {
        **SOLICITUD,
        "metodo": "4.2.2",
        "artefactos": [{
            "nombre": "Calentador B", "potencia_kw": 11.4, "tipo_artefacto": "B",
            "diametro_conector_cm": 12,
            "separacion_lateral_cm": 2.5, "separacion_posterior_cm": 2.5,
            "separacion_frontal_cm": 16,
        }],
    }
    creada = cliente.post("/v1/evaluaciones", json=solicitud, headers=APRENDIZ)
    assert creada.status_code == 201
    assert creada.json()["entradas"]["metodo"] == "4.2.2"
    detalle = cliente.get(creada.headers["location"], headers=APRENDIZ).json()
    assert detalle["entradas"]["artefactos"][0]["tipo_artefacto"] == "B"


def test_idempotency_key_no_duplica(cliente: TestClient) -> None:
    cabeceras = dict(APRENDIZ, **{"Idempotency-Key": "clave-1"})
    primera = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras)
    segunda = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras)
    assert primera.json()["id"] == segunda.json()["id"]


def test_idempotency_key_no_comparte_evaluaciones_entre_aprendices(cliente: TestClient) -> None:
    primera = cliente.post(
        "/v1/evaluaciones",
        json=SOLICITUD,
        headers={**APRENDIZ, "Idempotency-Key": "clave-compartida"},
    )
    segunda = cliente.post(
        "/v1/evaluaciones",
        json=SOLICITUD,
        headers={**OTRO_APRENDIZ, "Idempotency-Key": "clave-compartida"},
    )
    assert segunda.status_code == 201
    assert segunda.json()["aprendiz_id"] == "aprendiz-2"
    assert segunda.json()["id"] != primera.json()["id"]


def test_idempotency_key_se_puede_reutilizar_tras_borrar(cliente: TestClient) -> None:
    cabeceras = {**APRENDIZ, "Idempotency-Key": "clave-borrada"}
    primera = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras).json()
    assert cliente.delete(f"/v1/evaluaciones/{primera['id']}", headers=APRENDIZ).status_code == 204
    segunda = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=cabeceras)
    assert segunda.status_code == 201
    assert segunda.json()["id"] != primera["id"]


def test_el_aprendiz_solo_ve_lo_suyo(cliente: TestClient) -> None:
    cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ)
    cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=OTRO_APRENDIZ)

    propio = cliente.get("/v1/evaluaciones", headers=APRENDIZ).json()
    assert propio["total"] == 1

    todos = cliente.get("/v1/evaluaciones", headers=ADMIN).json()
    assert todos["total"] == 2


def test_instructor_lista_solo_su_ficha_aunque_solicite_otra(cliente: TestClient) -> None:
    for ficha in ("ficha-1", "ficha-2"):
        cliente.post(
            "/v1/evaluaciones",
            json={**SOLICITUD, "ficha_id": ficha},
            headers=APRENDIZ,
        )

    respuesta = cliente.get("/v1/evaluaciones", params={"ficha_id": "ficha-2"}, headers=INSTRUCTOR)
    assert respuesta.status_code == 403


def test_instructor_lista_y_consulta_solo_su_ficha(cliente: TestClient) -> None:
    propias = cliente.post(
        "/v1/evaluaciones", json={**SOLICITUD, "ficha_id": "ficha-1"}, headers=APRENDIZ
    ).json()
    cliente.post("/v1/evaluaciones", json={**SOLICITUD, "ficha_id": "ficha-2"}, headers=APRENDIZ)
    respuesta = cliente.get("/v1/evaluaciones", headers=INSTRUCTOR)
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["items"][0]["id"] == propias["id"]
    assert cliente.get(f"/v1/evaluaciones/{propias['id']}", headers=INSTRUCTOR).status_code == 200


def test_instructor_sin_ficha_no_lista_evaluaciones(cliente: TestClient) -> None:
    cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ)
    respuesta = cliente.get(
        "/v1/evaluaciones", headers={"X-Dev-Usuario": "instructor-2", "X-Dev-Rol": "instructor"}
    )
    assert respuesta.status_code == 403


def test_instructor_no_consulta_detalle_de_otra_ficha(cliente: TestClient) -> None:
    creada = cliente.post(
        "/v1/evaluaciones", json={**SOLICITUD, "ficha_id": "ficha-2"}, headers=APRENDIZ
    ).json()
    respuesta = cliente.get(f"/v1/evaluaciones/{creada['id']}", headers=INSTRUCTOR)
    assert respuesta.status_code == 404


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


def test_instructor_no_elimina_evaluacion_de_otra_ficha(cliente: TestClient) -> None:
    creada = cliente.post(
        "/v1/evaluaciones", json={**SOLICITUD, "ficha_id": "ficha-2"}, headers=APRENDIZ
    ).json()
    respuesta = cliente.delete(f"/v1/evaluaciones/{creada['id']}", headers=INSTRUCTOR)
    assert respuesta.status_code == 404
    assert cliente.get(f"/v1/evaluaciones/{creada['id']}", headers=ADMIN).status_code == 200


def test_reporte_pdf_declara_no_implementado(cliente: TestClient) -> None:
    creada = cliente.post("/v1/evaluaciones", json=SOLICITUD, headers=APRENDIZ).json()
    respuesta = cliente.get(f"/v1/evaluaciones/{creada['id']}/reporte.pdf", headers=APRENDIZ)
    assert respuesta.status_code == 501
    assert respuesta.json()["code"] == "regla_no_implementada"


def test_instructor_no_consulta_reporte_de_otra_ficha(cliente: TestClient) -> None:
    creada = cliente.post(
        "/v1/evaluaciones", json={**SOLICITUD, "ficha_id": "ficha-2"}, headers=APRENDIZ
    ).json()
    respuesta = cliente.get(f"/v1/evaluaciones/{creada['id']}/reporte.pdf", headers=INSTRUCTOR)
    assert respuesta.status_code == 404


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
