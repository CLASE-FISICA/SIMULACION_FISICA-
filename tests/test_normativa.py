"""Las constantes normativas se vigilan solas: cada una cita su numeral."""

from __future__ import annotations

import pytest
from app.domain import constants as C


def test_toda_constante_cita_su_numeral() -> None:
    for constante in C.NORMATIVA.values():
        assert constante.numeral.strip(), f"{constante.clave} no tiene numeral"
        assert constante.descripcion.strip(), f"{constante.clave} no tiene descripción"


def test_valores_normativos() -> None:
    esperados = {
        "volumen_minimo_por_kw": 3.4,
        "area_mismo_piso_cm2_kw": 22.0,
        "area_mismo_piso_min_cm2": 645.0,
        "area_distinto_piso_cm2_kw": 44.0,
        "area_directo_cm2_kw": 6.0,
        "area_conducto_horizontal_cm2_kw": 11.0,
        "area_metodo_2_cm2_kw": 11.0,
        "area_anexo_d_cm2_kw": 150.0,
        "caudal_mecanico_m3_min_kw": 0.034,
        "dimension_minima_abertura_cm": 8.0,
        "factor_obturacion_rejilla": 0.6,
        "margen_muebles": 0.2,
        "altitud_anexo_d_msnm": 260.0,
    }
    for clave, valor in esperados.items():
        assert C.NORMATIVA[clave].valor == pytest.approx(valor), clave


def test_area_minima_se_deriva_de_la_dimension() -> None:
    """64 cm² no es un número mágico: es 8 cm al cuadrado."""
    lado = C.DIMENSION_MINIMA_ABERTURA_CM.valor
    assert C.area_minima_abertura_cm2() == pytest.approx(64.0)
    assert C.area_minima_abertura_cm2() == pytest.approx(lado**2)
