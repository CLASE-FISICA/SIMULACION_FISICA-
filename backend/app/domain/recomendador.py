"""Árbol de decisión: recorre la norma y propone el método aplicable (BE-06).

Cada método queda aplicable, condicional (falta un dato para confirmarlo) o
descartado, con el motivo. Se propone el primero aplicable en el orden de la
norma: primero el aire del interior (4.1), luego la combinación (4.3), luego
el aire del exterior (4.2 y Anexo D) y por último el suministro mecánico (4.4).
"""

from collections.abc import Callable, Sequence

from app.domain.bitacora import Bitacora, fmt
from app.domain.modelos import (
    NOMBRE_METODO,
    NUMERAL_METODO,
    Advertencia,
    Artefacto,
    ContextoRecinto,
    EstadoMetodo,
    Metodo,
    Nivel,
    OpcionMetodo,
    Recinto,
    Recomendacion,
    ResultadoEstandar,
    TipoRecinto,
)
from app.domain.normativa import (
    ALTITUD_MAXIMA_ANEXO_D,
    SEPARACION_M2_FRONTAL,
    SEPARACION_M2_LATERAL_POSTERIOR,
    VOLUMEN_POR_KW,
)

ORDEN: tuple[Metodo, ...] = (
    Metodo.MISMO_PISO,
    Metodo.DIFERENTES_PISOS,
    Metodo.COMBINACION,
    Metodo.M1_DIRECTA,
    Metodo.M2_UNA_ABERTURA,
    Metodo.M1_CONDUCTO_VERTICAL,
    Metodo.M1_CONDUCTO_HORIZONTAL,
    Metodo.ANEXO_D,
    Metodo.SUMINISTRO_MECANICO,
)

_Evaluacion = tuple[EstadoMetodo, str]
A, C, N = EstadoMetodo.APLICABLE, EstadoMetodo.CONDICIONAL, EstadoMetodo.NO_APLICABLE


def restricciones_ubicacion(recinto: Recinto, artefactos: Sequence[Artefacto],
                            contexto: ContextoRecinto, b: Bitacora) -> bool:
    """Registra las restricciones de ubicación; True si la instalación no es admisible."""
    abiertos = [a.nombre for a in artefactos if a.cuenta_en_potencia]
    bloqueado = False
    if recinto.tipo in (TipoRecinto.DORMITORIO, TipoRecinto.BANO) and abiertos:
        lugar = "dormitorios" if recinto.tipo is TipoRecinto.DORMITORIO else "baños o duchas"
        b.advertir(Nivel.BLOQUEANTE,
                   f"En {lugar} solo se admiten artefactos de cámara estanca (Tipo C); "
                   f"retire {', '.join(f'«{n}»' for n in abiertos)}.",
                   "Restricciones de ubicación")
        bloqueado = True
    if recinto.tipo is TipoRecinto.BAJO_PRIMER_SOTANO:
        b.advertir(Nivel.BLOQUEANTE,
                   "No se deben instalar artefactos a gas por debajo del primer sótano.",
                   "Restricciones de ubicación")
        bloqueado = True
    if recinto.tipo is TipoRecinto.PRIMER_SOTANO:
        if contexto.gas_mas_denso_que_aire:
            b.advertir(Nivel.BLOQUEANTE,
                       "Con un gas más denso que el aire (GLP) no se deben instalar artefactos "
                       "en un primer sótano.", "Restricciones de ubicación")
            bloqueado = True
        elif contexto.gas_mas_denso_que_aire is None:
            b.advertir(Nivel.ADVERTENCIA,
                       "En un primer sótano solo se admite gas menos denso que el aire (gas "
                       "natural); confirme el tipo de gas.", "Restricciones de ubicación")
    return bloqueado


def _segun(dato: bool | None, si: str, no: str, falta: str) -> _Evaluacion:
    if dato is None:
        return C, falta
    return (A, si) if dato else (N, no)


def _interior(dato: bool | None, piso: str, volumen_ok: bool | None) -> _Evaluacion:
    if dato is False:
        return N, f"No hay espacios comunicados en {piso}."
    if volumen_ok is False:
        return N, ("El volumen combinado no alcanza 3,4 m³/kW; las aberturas interiores no "
                   "bastan (ver 4.3).")
    if dato and volumen_ok:
        return A, f"Los espacios comunicados en {piso} suman el volumen del método estándar."
    return C, (f"Aplica si hay espacios comunicados en {piso} y el volumen combinado alcanza "
               "3,4 m³/kW.")


def _separaciones_ok(artefactos: Sequence[Artefacto]) -> bool | None:
    lat, frente = SEPARACION_M2_LATERAL_POSTERIOR.valor, SEPARACION_M2_FRONTAL.valor
    completos = True
    for a in (x for x in artefactos if x.cuenta_en_potencia):
        medidas = ((a.separacion_lateral_cm, lat), (a.separacion_posterior_cm, lat),
                   (a.separacion_frontal_cm, frente))
        for valor, minimo in medidas:
            if valor is None:
                completos = False
            elif valor < minimo:
                return False
    return True if completos else None


def recomendar(estandar: ResultadoEstandar, artefactos: Sequence[Artefacto],
               contexto: ContextoRecinto, bloqueado: bool = False) -> Recomendacion:
    estandar_opcion = OpcionMetodo(
        metodo=Metodo.ESTANDAR, nombre=NOMBRE_METODO[Metodo.ESTANDAR], numeral="4.1.1",
        estado=A if estandar.cumple else N,
        motivo=("El volumen del recinto alcanza 3,4 m³/kW." if estandar.cumple
                else "El volumen del recinto no alcanza 3,4 m³/kW."),
    )
    if bloqueado:
        return Recomendacion(
            metodo_propuesto=None, alternativas=(), descartados=(estandar_opcion,),
            advertencias=(Advertencia(
                nivel=Nivel.BLOQUEANTE,
                mensaje="La ubicación de los artefactos no es admisible: ningún método de "
                        "ventilación la corrige.",
                numeral="Restricciones de ubicación"),),
        )
    if estandar.cumple:
        return Recomendacion(metodo_propuesto=Metodo.ESTANDAR, alternativas=(),
                             descartados=(), advertencias=())

    ctx = contexto
    p = estandar.potencia_total_kw
    volumen_ok: bool | None = None
    if ctx.volumen_espacios_comunicados_m3 is not None:
        combinado = estandar.volumen_util_m3 + ctx.volumen_espacios_comunicados_m3
        volumen_ok = combinado / p >= VOLUMEN_POR_KW.valor

    exterior_posible: bool | None
    salidas = (ctx.tiene_muro_exterior, ctx.permite_conducto_vertical,
               ctx.permite_conducto_horizontal)
    if any(s is True for s in salidas):
        exterior_posible = True
    elif all(s is False for s in salidas):
        exterior_posible = False
    else:
        exterior_posible = None

    hay_comunicados: bool | None
    pisos = (ctx.espacios_comunicados_mismo_piso, ctx.espacios_comunicados_diferentes_pisos)
    if any(x is True for x in pisos):
        hay_comunicados = True
    elif all(x is False for x in pisos):
        hay_comunicados = False
    else:
        hay_comunicados = None

    def combinacion() -> _Evaluacion:
        if hay_comunicados is False:
            return N, "No hay espacios interiores comunicados que aporten aire."
        if exterior_posible is False:
            return N, "El recinto no puede comunicarse con el exterior."
        if volumen_ok:
            return N, "Basta con las aberturas interiores del numeral 4.1.2."
        if hay_comunicados and exterior_posible:
            return A, ("El interior aporta parte del aire y una abertura exterior reducida "
                       "completa el resto.")
        return C, "Aplica si hay espacios interiores comunicados y salida al exterior."

    def metodo_2() -> _Evaluacion:
        estado, motivo = _segun(ctx.tiene_muro_exterior,
                                "El recinto tiene muro hacia el exterior.",
                                "El recinto no tiene muro hacia el exterior.",
                                "Aplica si el recinto tiene muro hacia el exterior.")
        separaciones = _separaciones_ok(artefactos)
        if separaciones is False:
            return N, ("Un artefacto no tiene 2,5 cm de separación a los lados y atrás o "
                       "16 cm al frente.")
        if estado is A and separaciones is None:
            return C, motivo + " Falta confirmar las separaciones de los artefactos."
        return estado, motivo

    def anexo_d() -> _Evaluacion:
        limite = ALTITUD_MAXIMA_ANEXO_D.valor
        if ctx.altitud_msnm is None:
            return C, f"Aplica si el recinto está a menos de {fmt(limite)} msnm."
        if ctx.altitud_msnm >= limite:
            return N, (f"El recinto está a {fmt(ctx.altitud_msnm)} msnm, "
                       f"no a menos de {fmt(limite)}.")
        if ctx.tiene_muro_exterior is False:
            return N, "El recinto no tiene muro hacia el exterior para la abertura."
        return A, f"El recinto está a {fmt(ctx.altitud_msnm)} msnm."

    reglas: dict[Metodo, Callable[[], _Evaluacion]] = {
        Metodo.MISMO_PISO: lambda: _interior(ctx.espacios_comunicados_mismo_piso,
                                             "el mismo piso", volumen_ok),
        Metodo.DIFERENTES_PISOS: lambda: _interior(ctx.espacios_comunicados_diferentes_pisos,
                                                   "diferentes pisos", volumen_ok),
        Metodo.COMBINACION: combinacion,
        Metodo.M1_DIRECTA: lambda: _segun(
            ctx.tiene_muro_exterior,
            "El recinto tiene muro hacia el exterior para dos aberturas.",
            "El recinto no tiene muro hacia el exterior.",
            "Aplica si el recinto tiene muro hacia el exterior para dos aberturas."),
        Metodo.M2_UNA_ABERTURA: metodo_2,
        Metodo.M1_CONDUCTO_VERTICAL: lambda: _segun(
            ctx.permite_conducto_vertical, "Se puede construir un conducto vertical.",
            "No se puede construir un conducto vertical.",
            "Aplica si se puede llevar un conducto vertical hasta el exterior."),
        Metodo.M1_CONDUCTO_HORIZONTAL: lambda: _segun(
            ctx.permite_conducto_horizontal, "Se puede construir un conducto horizontal.",
            "No se puede construir un conducto horizontal.",
            "Aplica si se puede llevar un conducto horizontal hasta el exterior."),
        Metodo.ANEXO_D: anexo_d,
        Metodo.SUMINISTRO_MECANICO: lambda: _segun(
            ctx.permite_suministro_mecanico, "Se admite un ventilador de suministro.",
            "No se admite suministro mecánico.",
            "Aplica si se puede instalar un ventilador enclavado con los artefactos."),
    }

    opciones: list[OpcionMetodo] = []
    for metodo in ORDEN:
        estado, motivo = reglas[metodo]()
        opciones.append(OpcionMetodo(metodo=metodo, nombre=NOMBRE_METODO[metodo],
                                     numeral=NUMERAL_METODO[metodo], estado=estado,
                                     motivo=motivo))

    aplicables = [o for o in opciones if o.estado is A]
    condicionales = [o for o in opciones if o.estado is C]
    candidatas = aplicables + condicionales
    propuesta = candidatas[0] if candidatas else None

    advertencias: list[Advertencia] = []
    if propuesta is None:
        advertencias.append(Advertencia(
            nivel=Nivel.BLOQUEANTE,
            mensaje="Ningún método de ventilación es aplicable con los datos dados.",
        ))
    elif propuesta.estado is C:
        advertencias.append(Advertencia(
            nivel=Nivel.ADVERTENCIA,
            mensaje=f"El método propuesto es condicional: {propuesta.motivo}",
            numeral=propuesta.numeral,
        ))

    return Recomendacion(
        metodo_propuesto=propuesta.metodo if propuesta else None,
        alternativas=tuple(o for o in candidatas if o is not propuesta),
        descartados=(estandar_opcion, *(o for o in opciones if o.estado is N)),
        advertencias=tuple(advertencias),
    )
