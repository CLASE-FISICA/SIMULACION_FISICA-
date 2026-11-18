"""Adaptador explícito entre el contrato v1 y el motor puro de BE1.

No serializa dataclasses del dominio directamente: el contrato conserva sus nombres y
la salida de dimensionamiento describe una propuesta, no certifica una instalación.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.api.dto import PasoDTO, RequerimientoDTO, ResultadoDTO, SolicitudEvaluacionDTO
from app.config import ajustes
from app.domain.modelos import (
    Artefacto,
    ContextoRecinto,
    EntradaEvaluacion,
    EntradaInvalida,
    Metodo,
    Nivel,
    OpcionesMetodo,
    Recinto,
    ResultadoDimensionamiento,
    TipoArtefacto,
    TipoRecinto,
)
from app.domain.motor import evaluar
from app.domain.normativa import Parametros


def _requerimiento(dimension: ResultadoDimensionamiento) -> RequerimientoDTO:
    return RequerimientoDTO(
        numeral=dimension.numeral,
        descripcion=dimension.nombre_metodo,
        area_libre_min_cm2=dimension.area_libre_cm2,
        cantidad=dimension.numero_aberturas,
        ubicacion="; ".join(dimension.ubicacion),
        rejilla_sugerida=(
            dimension.rejilla_comercial.nombre if dimension.rejilla_comercial else None
        ),
        elemento_sugerido=(
            str(dimension.conducto_comercial.diametro_pulg) + " pulgadas"
            if dimension.conducto_comercial else None
        ),
        cumple=None,
        nota="Dimensionamiento propuesto; no acredita que la abertura esté instalada.",
        caudal_min_m3h=dimension.caudal_total_m3h,
    )


def calcular(solicitud: SolicitudEvaluacionDTO) -> ResultadoDTO:
    recinto = solicitud.recinto
    if solicitud.metodo in ("4.2.2", "4.3"):
        for artefacto in solicitud.artefactos:
            if artefacto.circuito == "estanco":
                continue
            if artefacto.tipo_artefacto == "B" and artefacto.diametro_conector_cm is None:
                raise EntradaInvalida(
                    "artefactos.diametro_conector_cm",
                    "El Método 2 requiere el diámetro de cada conector Tipo B.",
                )
            if any(valor is None for valor in (
                artefacto.separacion_lateral_cm,
                artefacto.separacion_posterior_cm,
                artefacto.separacion_frontal_cm,
            )):
                raise EntradaInvalida(
                    "artefactos.separaciones",
                    "El Método 2 requiere separaciones laterales, posteriores y frontales.",
                )
    tipo = (
        TipoRecinto.PRIMER_SOTANO if recinto.nivel == "primer_sotano"
        else TipoRecinto.BAJO_PRIMER_SOTANO if recinto.nivel == "bajo_primer_sotano"
        else TipoRecinto.OTRO if recinto.tipo == "monoespacial"
        else TipoRecinto(recinto.tipo)
    )
    entrada = EntradaEvaluacion(
        recinto=Recinto(
            ancho=recinto.ancho_m, fondo=recinto.fondo_m, altura=recinto.alto_m, tipo=tipo
        ),
        artefactos=tuple(
            Artefacto(
                nombre=a.nombre,
                potencia=a.potencia_kw,
                tipo=(
                    TipoArtefacto.C if a.circuito == "estanco"
                    else TipoArtefacto.B if a.tipo_artefacto == "B"
                    else TipoArtefacto.A
                ),
                diametro_conector_cm=a.diametro_conector_cm,
                separacion_lateral_cm=a.separacion_lateral_cm,
                separacion_posterior_cm=a.separacion_posterior_cm,
                separacion_frontal_cm=a.separacion_frontal_cm,
            )
            for a in solicitud.artefactos
        ),
        metodo=Metodo(solicitud.metodo) if solicitud.metodo else None,
        opciones=OpcionesMetodo(
            volumen_espacios_comunicados_m3=recinto.volumen_comunicado_m3,
            altitud_msnm=recinto.altitud_msnm,
            extraccion_cocina_m3h=solicitud.opciones.extraccion_cocina_m3h,
        ),
        contexto=ContextoRecinto(
            volumen_espacios_comunicados_m3=recinto.volumen_comunicado_m3,
            altitud_msnm=recinto.altitud_msnm,
            gas_mas_denso_que_aire=recinto.densidad_gas_relativa > 1,
        ),
        parametros=Parametros(restar_margen_muebles=solicitud.opciones.aplicar_margen_muebles),
    )
    resultado = evaluar(entrada)
    prohibido = any(
        a.nivel is Nivel.BLOQUEANTE and a.numeral == "Restricciones de ubicación"
        for a in resultado.advertencias
    )
    bloqueado = any(a.nivel is Nivel.BLOQUEANTE for a in resultado.advertencias)
    if bloqueado and not prohibido:
        motivo = next(a.mensaje for a in resultado.advertencias if a.nivel is Nivel.BLOQUEANTE)
        raise EntradaInvalida("metodo", motivo)
    # El motor puede dimensionar incluso un recinto prohibido. No presentar esa obra
    # como solución: la restricción de ubicación prevalece sobre cualquier método.
    dimension = None if bloqueado else resultado.dimensionamiento
    estandar = resultado.estandar
    requerimientos: list[RequerimientoDTO] = []
    if dimension is not None:
        requerimientos.append(_requerimiento(dimension))
        if dimension.aberturas_interiores is not None:
            requerimientos.append(_requerimiento(dimension.aberturas_interiores))
    veredicto = "no_permitido" if prohibido else "cumple" if estandar.cumple else "no_cumple"
    advertencias = [a.mensaje for a in resultado.advertencias]
    if recinto.tipo == "monoespacial":
        advertencias.append("Los recintos monoespaciales se rigen además por el Anexo B de la NTC 3631.")
    if recinto.nivel == "primer_sotano" and not prohibido:
        advertencias.append(
            "En primer sótano con gas menos denso que el aire se requiere ventilación "
            "mediante uno de los métodos del numeral 4; el volumen estándar no basta."
        )
    if (
        resultado.recomendacion is not None
        and resultado.recomendacion.metodo_propuesto
        and not resultado.recomendacion.advertencias
    ):
        advertencias.append(
            f"Método propuesto por el motor: {resultado.recomendacion.metodo_propuesto.value}."
        )
    return ResultadoDTO(
        veredicto=veredicto,
        metodo=dimension.nombre_metodo if dimension else "Método estándar",
        numeral=dimension.numeral if dimension else estandar.numeral,
        resumen=(
            "Instalación no permitida por restricciones de ubicación." if prohibido
            else estandar.veredicto
        ),
        volumen_m3=estandar.volumen_m3,
        volumen_efectivo_m3=estandar.volumen_util_m3,
        potencia_agregada_kw=estandar.potencia_total_kw,
        potencia_excluida_kw=estandar.potencia_excluida_kw,
        volumen_requerido_m3=estandar.volumen_requerido_m3,
        relacion_m3_kw=estandar.relacion_m3_kw,
        pasos=[
            PasoDTO(
                numeral=p.numeral or "Práctica de diseño",
                titulo=p.descripcion,
                detalle=f"{p.formula}: {p.sustitucion}",
                valor=f"{p.resultado} {p.unidad}".strip(),
            )
            for p in resultado.pasos
        ],
        requerimientos=requerimientos,
        advertencias=advertencias,
        norma_version=ajustes.norma_version,
        motor_version=resultado.version_motor,
        generado_en=datetime.now(UTC),
    )
