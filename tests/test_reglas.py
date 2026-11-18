"""Reglas del motor probadas por separado: exclusiones, bloqueos y advertencias."""

from __future__ import annotations

import pytest
from app.domain.engine import evaluar
from app.domain.errors import SinArtefactos
from app.domain.models import (
    Artefacto,
    Circuito,
    Nivel,
    Opciones,
    Recinto,
    TipoRecinto,
    Veredicto,
)


def recinto(**kw: object) -> Recinto:
    base = {"ancho_m": 3.0, "fondo_m": 3.0, "alto_m": 2.6}
    base.update(kw)
    return Recinto(**base)  # type: ignore[arg-type]


def test_artefacto_tipo_c_no_suma_potencia() -> None:
    """Numeral 4.1.1, nota: los artefactos de cámara estanca quedan fuera del cálculo."""
    artefactos = [
        Artefacto(nombre="Calentador estanco", potencia_kw=24.0, circuito=Circuito.ESTANCO),
        Artefacto(nombre="Cocina", potencia_kw=5.0),
    ]
    resultado = evaluar(recinto(), artefactos)

    assert resultado.potencia_agregada_kw == pytest.approx(5.0)
    assert resultado.potencia_excluida_kw == pytest.approx(24.0)
    # 23,4 m³ / 5 kW = 4,68 m³/kW: cumple solo porque el estanco no cuenta.
    assert resultado.relacion_m3_kw == pytest.approx(4.68, abs=0.001)
    assert resultado.veredicto is Veredicto.CUMPLE


def test_solo_artefactos_estancos_no_requiere_ventilacion() -> None:
    artefactos = [Artefacto(nombre="Caldera", potencia_kw=30.0, circuito=Circuito.ESTANCO)]
    resultado = evaluar(recinto(ancho_m=1.0, fondo_m=1.0, alto_m=2.0), artefactos)

    assert resultado.veredicto is Veredicto.CUMPLE
    assert resultado.relacion_m3_kw is None
    assert "circuito estanco" in resultado.resumen


def test_dormitorio_con_circuito_abierto_no_se_permite() -> None:
    resultado = evaluar(
        recinto(tipo=TipoRecinto.DORMITORIO),
        [Artefacto(nombre="Estufa", potencia_kw=7.0)],
    )

    assert resultado.veredicto is Veredicto.NO_PERMITIDO
    assert resultado.metodo == "Restricciones de ubicación"
    assert any("dormitorio" in p.titulo.lower() for p in resultado.pasos)


def test_dormitorio_con_estanco_si_se_evalua() -> None:
    resultado = evaluar(
        recinto(tipo=TipoRecinto.DORMITORIO),
        [Artefacto(nombre="Calentador", potencia_kw=7.0, circuito=Circuito.ESTANCO)],
    )

    assert resultado.veredicto is not Veredicto.NO_PERMITIDO


def test_bajo_el_primer_sotano_no_se_permite() -> None:
    resultado = evaluar(
        recinto(nivel=Nivel.BAJO_PRIMER_SOTANO),
        [Artefacto(nombre="Calentador", potencia_kw=11.4)],
    )

    assert resultado.veredicto is Veredicto.NO_PERMITIDO
    assert "sótano" in resultado.resumen


def test_primer_sotano_con_gas_denso_no_se_permite() -> None:
    resultado = evaluar(
        recinto(nivel=Nivel.PRIMER_SOTANO, densidad_gas_relativa=1.5),
        [Artefacto(nombre="Calentador", potencia_kw=11.4)],
    )

    assert resultado.veredicto is Veredicto.NO_PERMITIDO
    assert "denso" in resultado.resumen


def test_primer_sotano_con_gas_ligero_advierte() -> None:
    resultado = evaluar(
        recinto(nivel=Nivel.PRIMER_SOTANO, densidad_gas_relativa=0.6, ancho_m=9.0, fondo_m=9.0),
        [Artefacto(nombre="Calentador", potencia_kw=5.0)],
    )

    assert resultado.veredicto is Veredicto.CUMPLE
    assert any("primer sótano" in a for a in resultado.advertencias)


def test_recinto_bajo_260_msnm_advierte_anexo_d() -> None:
    resultado = evaluar(
        recinto(altitud_msnm=100.0),
        [Artefacto(nombre="Cocina", potencia_kw=5.0)],
    )

    assert any("Anexo D" in a for a in resultado.advertencias)


def test_bano_y_monoespacial_advierte() -> None:
    for tipo in (TipoRecinto.BANO, TipoRecinto.MONOESPACIAL):
        resultado = evaluar(recinto(tipo=tipo), [Artefacto(nombre="Calentador", potencia_kw=5.0)])
        assert resultado.advertencias


def test_margen_de_muebles_reduce_el_volumen_efectivo() -> None:
    """Un recinto de 20 m³ con 5 kW está justo por encima del umbral.

    20 m³ ÷ 5 kW = 4,00 m³/kW: cumple. Con el descuento del 20 % quedan 16 m³ y
    la relación cae a 3,20 m³/kW: no cumple. Es el caso que demuestra que la opción
    cambia el veredicto, y por eso el informe debe declararla.
    """
    artefactos = [Artefacto(nombre="Cocina", potencia_kw=5.0)]
    sala = Recinto(ancho_m=4.0, fondo_m=2.5, alto_m=2.0)
    sin_margen = evaluar(sala, artefactos)
    con_margen = evaluar(sala, artefactos, Opciones(aplicar_margen_muebles=True))

    assert sin_margen.volumen_efectivo_m3 == pytest.approx(20.0)
    assert con_margen.volumen_efectivo_m3 == pytest.approx(16.0)
    assert sin_margen.veredicto is Veredicto.CUMPLE
    assert con_margen.veredicto is Veredicto.NO_CUMPLE
    assert any("20 %" in a for a in con_margen.advertencias)


def test_sin_artefactos_es_error() -> None:
    with pytest.raises(SinArtefactos):
        evaluar(recinto(), [])


def test_todo_veredicto_cita_su_numeral() -> None:
    """Sin numeral no hay auditoría: la traza es obligatoria."""
    resultado = evaluar(recinto(), [Artefacto(nombre="Cocina", potencia_kw=5.0)])

    assert resultado.numeral
    assert resultado.pasos
    assert all(p.numeral for p in resultado.pasos)
