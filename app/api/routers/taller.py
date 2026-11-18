"""Taller: corrección de la respuesta del aprendiz.

No se corrige lo que no está resuelto: dos de los tres ejercicios del libro no tienen
respuesta esperada (DO04). Devolver un veredicto inventado sería peor que decir que aún
no está disponible.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.dto import IntentoDTO, SolicitudIntentoDTO
from app.api.errors import Problema
from app.api.security import UsuarioActual
from app.infra.taller import EJERCICIOS

router = APIRouter(prefix="/v1/taller", tags=["taller"])


@router.post(
    "/{ejercicio_id}/intentos",
    response_model=IntentoDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registra la respuesta del aprendiz y la corrige",
)
def registrar(ejercicio_id: str, solicitud: SolicitudIntentoDTO, usuario: UsuarioActual) -> IntentoDTO:
    ejercicio = EJERCICIOS.get(ejercicio_id)
    if ejercicio is None:
        raise Problema(
            status=404,
            code="no_encontrado",
            title="El recurso no existe",
            detail="El ejercicio no existe.",
        )
    if ejercicio.esperado is None:
        raise Problema(
            status=409,
            code="regla_no_implementada",
            title="Ejercicio sin respuesta esperada",
            detail=(
                "Este ejercicio todavía no tiene solución validada por el instructor. "
                "Se corrige cuando Documentación cargue la respuesta esperada."
            ),
        )
    if solicitud.respuesta.relacion_m3_kw is None and solicitud.respuesta.veredicto is None:
        raise Problema(
            status=422,
            code="validacion",
            title="Entrada inválida",
            detail="Debe enviar al menos la relación m³/kW o el veredicto.",
        )

    esperado = ejercicio.esperado
    correcto = True
    detalles: list[str] = []

    if solicitud.respuesta.relacion_m3_kw is not None:
        referencia = esperado.relacion_m3_kw
        if referencia is None:
            correcto = False
            detalles.append("El ejercicio no tiene relación de referencia.")
        else:
            tolerancia = abs(referencia) * ejercicio.tolerancia_relativa
            if abs(solicitud.respuesta.relacion_m3_kw - referencia) > tolerancia:
                correcto = False
                detalles.append(
                    f"Esperado {referencia:.3f} m³/kW; recibido "
                    f"{solicitud.respuesta.relacion_m3_kw:.3f} m³/kW."
                )

    if (
        solicitud.respuesta.veredicto is not None
        and esperado.veredicto is not None
        and solicitud.respuesta.veredicto != esperado.veredicto
    ):
        correcto = False
        detalles.append(
            f"El veredicto esperado es «{esperado.veredicto}» y llegó «{solicitud.respuesta.veredicto}»."
        )

    retroalimentacion = (
        "Respuesta correcta. El recinto no cumple el método estándar."
        if correcto
        else "Revisar el cálculo. " + " ".join(detalles)
    )

    return IntentoDTO(
        id=str(uuid.uuid4()),
        correcto=correcto,
        retroalimentacion=retroalimentacion,
    )
