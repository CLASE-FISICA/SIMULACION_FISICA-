"""Mapeo entre el dominio y el contrato.

Existe porque el DTO es una copia y no el modelo del dominio (ADR-003, D6). Es
deliberadamente explícito y campo por campo: si el dominio cambia, este archivo no
compila y nos enteramos aquí, no en el frontend.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.api.dto import (
    ArtefactoDTO,
    EvaluacionGuardadaDTO,
    OpcionesDTO,
    PasoDTO,
    RecintoDTO,
    ResultadoDTO,
    SolicitudEvaluacionDTO,
)
from app.domain.models import (
    Artefacto,
    Circuito,
    Nivel,
    Opciones,
    Paso,
    Recinto,
    Resultado,
    TipoRecinto,
)
from app.infra.repositorio import EvaluacionAlmacenada


def a_dominio(
    solicitud: SolicitudEvaluacionDTO,
) -> tuple[Recinto, list[Artefacto], Opciones]:
    recinto = Recinto(
        ancho_m=solicitud.recinto.ancho_m,
        fondo_m=solicitud.recinto.fondo_m,
        alto_m=solicitud.recinto.alto_m,
        tipo=TipoRecinto(solicitud.recinto.tipo),
        nivel=Nivel(solicitud.recinto.nivel),
        altitud_msnm=solicitud.recinto.altitud_msnm,
        densidad_gas_relativa=solicitud.recinto.densidad_gas_relativa,
        volumen_comunicado_m3=solicitud.recinto.volumen_comunicado_m3,
    )
    artefactos = [
        Artefacto(
            nombre=a.nombre,
            potencia_kw=a.potencia_kw,
            circuito=Circuito(a.circuito),
            diametro_conector_cm=a.diametro_conector_cm,
        )
        for a in solicitud.artefactos
    ]
    opciones = Opciones(aplicar_margen_muebles=solicitud.opciones.aplicar_margen_muebles)
    return recinto, artefactos, opciones


def _paso(paso: Paso) -> PasoDTO:
    return PasoDTO(
        numeral=paso.numeral,
        titulo=paso.titulo,
        detalle=paso.detalle,
        valor=paso.valor,
    )


def a_dto(
    resultado: Resultado,
    *,
    norma_version: str,
    motor_version: str,
    generado_en: datetime | None = None,
) -> ResultadoDTO:
    return ResultadoDTO(
        veredicto=resultado.veredicto.value,
        metodo=resultado.metodo,
        numeral=resultado.numeral,
        resumen=resultado.resumen,
        volumen_m3=resultado.volumen_m3,
        volumen_efectivo_m3=resultado.volumen_efectivo_m3,
        potencia_agregada_kw=resultado.potencia_agregada_kw,
        potencia_excluida_kw=resultado.potencia_excluida_kw,
        volumen_requerido_m3=resultado.volumen_requerido_m3,
        relacion_m3_kw=resultado.relacion_m3_kw,
        pasos=[_paso(p) for p in resultado.pasos],
        requerimientos=[],
        advertencias=list(resultado.advertencias),
        norma_version=norma_version,
        motor_version=motor_version,
        generado_en=generado_en or datetime.now(UTC),
    )


def evaluacion_a_dto(almacenada: EvaluacionAlmacenada) -> EvaluacionGuardadaDTO:
    entradas = almacenada.entradas
    return EvaluacionGuardadaDTO(
        id=almacenada.id,
        creada_en=almacenada.creada_en,
        ficha_id=entradas.ficha_id,
        aprendiz_id=almacenada.aprendiz_id,
        entradas=SolicitudEvaluacionDTO(
            recinto=RecintoDTO(**entradas.recinto.model_dump()),
            artefactos=[ArtefactoDTO(**a.model_dump()) for a in entradas.artefactos],
            opciones=OpcionesDTO(**entradas.opciones.model_dump()),
            ficha_id=entradas.ficha_id,
        ),
        resultado=almacenada.resultado,
    )
