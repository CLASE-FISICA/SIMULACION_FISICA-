"""El contrato es la fuente de verdad: si el código se aparta, esta prueba falla.

Decisión D1 del ADR-003. Compara las rutas y métodos del YAML versionado contra el
esquema que genera FastAPI. Si alguien añade o quita una ruta sin actualizar el contrato,
el build se rompe aquí y no en el frontend tres semanas después.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from app.api.main import app

CONTRATO = Path(__file__).resolve().parent.parent / "docs" / "contrato" / "openapi.yaml"
METODOS = {"get", "post", "put", "patch", "delete"}


def _firmas_openapi(paths: dict[str, dict[str, object]]) -> set[str]:
    firmas: set[str] = set()
    for ruta, operaciones in paths.items():
        for metodo in operaciones:
            if metodo in METODOS:
                firmas.add(f"{metodo.upper()} {ruta}")
    return firmas


@pytest.fixture(scope="module")
def contrato() -> dict[str, object]:
    assert CONTRATO.exists(), f"No existe el contrato en {CONTRATO}"
    with CONTRATO.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def generado() -> dict[str, object]:
    return app.openapi()


def test_mismas_rutas_y_metodos(contrato: dict, generado: dict) -> None:
    esperadas = _firmas_openapi(contrato["paths"])
    reales = _firmas_openapi(generado["paths"])

    faltan_en_codigo = esperadas - reales
    sobran_en_codigo = reales - esperadas

    assert not faltan_en_codigo, f"Rutas del contrato sin implementar: {sorted(faltan_en_codigo)}"
    assert not sobran_en_codigo, f"Rutas implementadas fuera del contrato: {sorted(sobran_en_codigo)}"


def test_toda_ruta_del_contrato_tiene_summary(contrato: dict) -> None:
    for ruta, operaciones in contrato["paths"].items():
        for metodo, definicion in operaciones.items():
            if metodo in METODOS:
                assert definicion.get("summary"), f"{metodo} {ruta} sin summary"
                assert definicion.get("operationId"), f"{metodo} {ruta} sin operationId"


def test_catalogos_y_contenido_son_publicos(contrato: dict) -> None:
    """D10: el frontend necesita catálogos y contenido sin sesión."""
    publicas = {
        "/health",
        "/v1/normativa",
        "/v1/catalogos/rejillas",
        "/v1/catalogos/conductos",
        "/v1/catalogos/casos",
        "/v1/catalogos/parametros",
        "/v1/catalogos/listas",
        "/v1/contenido/{slug}",
    }
    for ruta in publicas:
        operaciones = contrato["paths"][ruta]
        assert any(
            d.get("security") == [] for m, d in operaciones.items() if m in METODOS
        ), f"{ruta} debería ser pública"


def test_evaluaciones_exigen_sesion(contrato: dict) -> None:
    operaciones = contrato["paths"]["/v1/evaluaciones/preview"]
    assert operaciones["post"].get("security") != []


def test_esquema_de_error_declarado(contrato: dict) -> None:
    esquema = contrato["components"]["schemas"]["Problema"]
    assert {"type", "title", "status"} <= set(esquema["required"])
    assert "code" in esquema["properties"]


def test_metodos_alternos_coinciden_con_el_contrato(contrato: dict) -> None:
    from app.domain.modelos import Metodo

    solicitud = contrato["components"]["schemas"]["SolicitudEvaluacion"]
    assert set(solicitud["properties"]["metodo"]["enum"]) == {m.value for m in Metodo}
