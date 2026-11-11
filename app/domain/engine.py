"""Motor de verificación de ventilación según NTC 3631.

Alcance de esta versión: numeral 4.1.1 y restricciones de ubicación.
Los métodos 4.1.2, 4.2.1, 4.2.2, 4.3, 4.4 y el Anexo D entran en las historias
siguientes; hasta entonces el resultado los anuncia como pendientes.
"""

from __future__ import annotations

from app.domain import constants as C
from app.domain.errors import SinArtefactos
from app.domain.models import (
    Artefacto,
    Circuito,
    Nivel,
    Opciones,
    Paso,
    Recinto,
    Resultado,
    TipoRecinto,
    Veredicto,
)


def _bloqueos(recinto: Recinto, artefactos: list[Artefacto]) -> tuple[Veredicto, str, list[Paso]]:
    """Restricciones de ubicación: casos en los que no se puede aprobar nada.

    Estas reglas no dependen del cálculo de aire: prohíben la instalación.
    """
    pasos: list[Paso] = []

    if recinto.nivel is Nivel.BAJO_PRIMER_SOTANO:
        pasos.append(
            Paso(
                numeral="Restricciones de ubicación",
                titulo="Nivel bajo el primer sótano",
                detalle=(
                    "En los recintos situados a un nivel inferior al primer sótano no se "
                    "deben instalar artefactos a gas."
                ),
                valor="no permitido",
            )
        )
        return (
            Veredicto.NO_PERMITIDO,
            "Instalación no permitida: el recinto está por debajo del primer sótano.",
            pasos,
        )

    if recinto.tipo is TipoRecinto.DORMITORIO and any(
        a.circuito is Circuito.ABIERTO for a in artefactos
    ):
        pasos.append(
            Paso(
                numeral="Restricciones de ubicación",
                titulo="Dormitorio con artefacto de circuito abierto",
                detalle=(
                    "Los recintos destinados a dormitorios no deben contener artefactos a gas "
                    "de circuito abierto; solo se admiten artefactos de circuito estanco (Tipo C)."
                ),
                valor="no permitido",
            )
        )
        return (
            Veredicto.NO_PERMITIDO,
            "Instalación no permitida: dormitorio con artefacto de circuito abierto.",
            pasos,
        )

    if recinto.nivel is Nivel.PRIMER_SOTANO and recinto.densidad_gas_relativa > 1.0:
        pasos.append(
            Paso(
                numeral="Restricciones de ubicación",
                titulo="Primer sótano con gas más denso que el aire",
                detalle=(
                    "Cuando el gas suministrado es más denso que el aire no se deben instalar "
                    "artefactos a gas en un primer sótano."
                ),
                valor="no permitido",
            )
        )
        return (
            Veredicto.NO_PERMITIDO,
            "Instalación no permitida: primer sótano con gas más denso que el aire.",
            pasos,
        )

    return Veredicto.CUMPLE, "", pasos


def evaluar(
    recinto: Recinto,
    artefactos: list[Artefacto],
    opciones: Opciones | None = None,
) -> Resultado:
    """Evalúa un recinto contra el método estándar del numeral 4.1.1."""
    if not artefactos:
        raise SinArtefactos(
            "El recinto debe tener al menos un artefacto para evaluar la demanda de aire."
        )

    opciones = opciones or Opciones()
    pasos: list[Paso] = []
    advertencias: list[str] = []

    bloqueo, resumen_bloqueo, pasos_bloqueo = _bloqueos(recinto, artefactos)
    if bloqueo is Veredicto.NO_PERMITIDO:
        return Resultado(
            veredicto=bloqueo,
            metodo="Restricciones de ubicación",
            numeral="Restricciones de ubicación",
            resumen=resumen_bloqueo,
            volumen_m3=round(recinto.volumen_bruto_m3, 3),
            volumen_efectivo_m3=round(recinto.volumen_bruto_m3, 3),
            potencia_agregada_kw=0.0,
            potencia_excluida_kw=0.0,
            volumen_requerido_m3=0.0,
            relacion_m3_kw=None,
            pasos=pasos_bloqueo,
            advertencias=["No se continúa con el cálculo de aire: la instalación está prohibida."],
        )

    # --- Volumen disponible (4.1.1) -----------------------------------------
    volumen_bruto = recinto.volumen_bruto_m3
    pasos.append(
        Paso(
            numeral="4.1.1",
            titulo="Volumen del recinto",
            detalle=f"{recinto.ancho_m:g} m × {recinto.fondo_m:g} m × {recinto.alto_m:g} m",
            valor=f"{volumen_bruto:.3f} m³",
        )
    )

    volumen_efectivo = volumen_bruto
    if opciones.aplicar_margen_muebles:
        volumen_efectivo = volumen_bruto * (1 - C.MARGEN_MUEBLES.valor)
        pasos.append(
            Paso(
                numeral="recomendación del instructor",
                titulo="Descuento por muebles y enseres",
                detalle=(
                    f"Se descuenta el {C.MARGEN_MUEBLES.valor:.0%} del volumen. "
                    "No está en la norma y el informe debe declararlo."
                ),
                valor=f"{volumen_efectivo:.3f} m³",
            )
        )
        advertencias.append(
            "Se aplicó el descuento del 20 % por muebles y enseres: recomendación del "
            "instructor, no texto de la NTC 3631."
        )

    # --- Potencia agregada (excluye Tipo C) ---------------------------------
    abiertos = [a for a in artefactos if a.circuito is Circuito.ABIERTO]
    estancos = [a for a in artefactos if a.circuito is Circuito.ESTANCO]
    potencia_agregada = sum(a.potencia_kw for a in abiertos)
    potencia_excluida = sum(a.potencia_kw for a in estancos)

    pasos.append(
        Paso(
            numeral="4.1.1",
            titulo="Potencia nominal agregada",
            detalle=(
                f"{len(abiertos)} artefacto(s) de circuito abierto: "
                + ", ".join(f"{a.nombre} {a.potencia_kw:g} kW" for a in abiertos)
                if abiertos
                else "Ningún artefacto de circuito abierto."
            ),
            valor=f"{potencia_agregada:.3f} kW",
        )
    )
    if estancos:
        pasos.append(
            Paso(
                numeral="4.1.1 nota",
                titulo="Potencia excluida",
                detalle=(
                    "Los artefactos de circuito estanco (Tipo C) no se suman a la potencia "
                    "agregada: "
                    + ", ".join(f"{a.nombre} {a.potencia_kw:g} kW" for a in estancos)
                ),
                valor=f"{potencia_excluida:.3f} kW",
            )
        )

    if potencia_agregada == 0:
        return Resultado(
            veredicto=Veredicto.CUMPLE,
            metodo="Excepción por artefactos Tipo C",
            numeral="4.1.1 nota",
            resumen=(
                "Todos los artefactos son de circuito estanco: no demandan aire del recinto "
                "y quedan fuera del alcance de la NTC 3631."
            ),
            volumen_m3=round(volumen_bruto, 3),
            volumen_efectivo_m3=round(volumen_efectivo, 3),
            potencia_agregada_kw=0.0,
            potencia_excluida_kw=round(potencia_excluida, 3),
            volumen_requerido_m3=0.0,
            relacion_m3_kw=None,
            pasos=pasos,
            advertencias=advertencias,
        )

    # --- Método estándar (4.1.1) -------------------------------------------
    volumen_requerido = C.VOLUMEN_MINIMO_POR_KW.valor * potencia_agregada
    relacion = volumen_efectivo / potencia_agregada
    cumple = relacion >= C.VOLUMEN_MINIMO_POR_KW.valor

    pasos.append(
        Paso(
            numeral="4.1.1",
            titulo="Volumen requerido",
            detalle=f"{C.VOLUMEN_MINIMO_POR_KW.valor:g} m³/kW × {potencia_agregada:.3f} kW",
            valor=f"{volumen_requerido:.3f} m³",
        )
    )
    pasos.append(
        Paso(
            numeral="4.1.1",
            titulo="Relación volumen / potencia",
            detalle=(
                f"{volumen_efectivo:.3f} m³ ÷ {potencia_agregada:.3f} kW "
                f"(umbral {C.VOLUMEN_MINIMO_POR_KW.valor:g} m³/kW)"
            ),
            valor=f"{relacion:.3f} m³/kW",
        )
    )

    if cumple:
        resumen = (
            f"Cumple el método estándar: {relacion:.2f} m³/kW frente al mínimo de "
            f"{C.VOLUMEN_MINIMO_POR_KW.valor:g} m³/kW."
        )
    else:
        resumen = (
            f"No cumple el método estándar: {relacion:.2f} m³/kW frente al mínimo de "
            f"{C.VOLUMEN_MINIMO_POR_KW.valor:g} m³/kW. "
            f"Faltan {volumen_requerido - volumen_efectivo:.2f} m³ o hay "
            f"{volumen_efectivo / C.VOLUMEN_MINIMO_POR_KW.valor:.2f} kW de más: "
            "se requiere una abertura según los numerales 4.1.2 o 4.2."
        )

    # --- Advertencias que no cambian el veredicto pero sí el informe --------
    if recinto.altitud_msnm < C.ALTITUD_ANEXO_D_MSNM.valor:
        advertencias.append(
            f"El recinto está a {recinto.altitud_msnm:g} msnm, por debajo de "
            f"{C.ALTITUD_ANEXO_D_MSNM.valor:g} msnm: si se requiere abertura al exterior aplica "
            f"el Anexo D ({C.AREA_ANEXO_D_CM2_KW.valor:g} cm²/kW)."
        )
    if recinto.volumen_comunicado_m3 > 0:
        advertencias.append(
            f"Se declararon {recinto.volumen_comunicado_m3:g} m³ de espacios comunicados: "
            "la ventilación combinada se resuelve con el numeral 4.3."
        )
    if recinto.nivel is Nivel.PRIMER_SOTANO:
        advertencias.append(
            "Recinto en primer sótano con gas menos denso que el aire: debe ventilarse además "
            "mediante uno de los métodos del numeral 4; el método estándar no basta."
        )
    if recinto.tipo is TipoRecinto.BANO:
        advertencias.append(
            "Los recintos de baño o ducha tienen requisitos propios además de este cálculo."
        )
    if recinto.tipo is TipoRecinto.MONOESPACIAL:
        advertencias.append(
            "Los recintos monoespaciales se rigen además por el Anexo B de la NTC 3631."
        )
    if not cumple:
        advertencias.append(
            "El dimensionamiento de aberturas, rejillas y conductos (numerales 4.1.2, 4.2.1, "
            "4.2.2, 4.3, 4.4 y Anexo D) todavía no está implementado en esta versión del motor."
        )

    return Resultado(
        veredicto=Veredicto.CUMPLE if cumple else Veredicto.NO_CUMPLE,
        metodo="Método estándar",
        numeral="4.1.1",
        resumen=resumen,
        volumen_m3=round(volumen_bruto, 3),
        volumen_efectivo_m3=round(volumen_efectivo, 3),
        potencia_agregada_kw=round(potencia_agregada, 3),
        potencia_excluida_kw=round(potencia_excluida, 3),
        volumen_requerido_m3=round(volumen_requerido, 3),
        relacion_m3_kw=round(relacion, 4),
        pasos=pasos,
        advertencias=advertencias,
    )
