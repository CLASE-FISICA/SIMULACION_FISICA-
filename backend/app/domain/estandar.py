"""Potencia agregada, volumen del recinto y método estándar, numeral 4.1.1 (BE-01)."""

from collections.abc import Sequence

from app.domain.bitacora import Bitacora, fmt
from app.domain.modelos import Artefacto, Nivel, Recinto, ResultadoEstandar, TipoArtefacto
from app.domain.normativa import VOLUMEN_POR_KW, Parametros
from app.domain.unidades import UnidadLongitud, UnidadPotencia, divisor_longitud, divisor_potencia

CUMPLE = "Cumple ventilación"
NO_CUMPLE = "No cumple ventilación"


def potencia_total(artefactos: Sequence[Artefacto], bitacora: Bitacora) -> tuple[float, float]:
    """Potencia nominal agregada en kW, sin los artefactos Tipo C.

    Devuelve (potencia que cuenta, potencia excluida).
    """
    sumandos: list[str] = []
    total = 0.0
    excluida = 0.0
    for artefacto in artefactos:
        kw = artefacto.potencia_kw
        if artefacto.unidad is not UnidadPotencia.KW:
            bitacora.paso(
                f"Potencia de «{artefacto.nombre}» en kW",
                f"P [{artefacto.unidad}] ÷ {fmt(divisor_potencia(artefacto.unidad), 3)}",
                f"{fmt(artefacto.potencia, 3)} ÷ {fmt(divisor_potencia(artefacto.unidad), 3)}",
                kw, "kW",
                origen="Taller práctico aprendices!E9, E11",
            )
        if artefacto.cuenta_en_potencia:
            total += kw
            sumandos.append(fmt(kw))
        else:
            excluida += kw
            bitacora.advertir(
                Nivel.INFO,
                f"«{artefacto.nombre}» es de cámara estanca (Tipo C): no cuenta en la "
                "potencia nominal agregada.",
                "4.1.1, nota",
            )
    bitacora.paso(
        "Potencia nominal agregada (sin artefactos Tipo C)",
        "P = Σ Pᵢ",
        " + ".join(sumandos) if sumandos else "0",
        total, "kW",
        numeral="4.1.1",
        origen="Taller práctico aprendices!E12",
    )
    return total, excluida


def volumen(recinto: Recinto, bitacora: Bitacora) -> float:
    if recinto.unidad is not UnidadLongitud.M:
        d = fmt(divisor_longitud(recinto.unidad), 0)
        bitacora.paso(
            "Dimensiones del recinto en metros",
            f"L [{recinto.unidad}] ÷ {d}",
            f"{fmt(recinto.ancho, 3)} ÷ {d}; {fmt(recinto.fondo, 3)} ÷ {d}; "
            f"{fmt(recinto.altura, 3)} ÷ {d}",
            f"{fmt(recinto.ancho_m, 3)} × {fmt(recinto.fondo_m, 3)} × {fmt(recinto.altura_m, 3)}",
            "m",
            origen="Taller práctico aprendices!E14, E17",
        )
    v = recinto.ancho_m * recinto.fondo_m * recinto.altura_m
    bitacora.paso(
        "Volumen del recinto",
        "V = ancho × fondo × altura",
        f"{fmt(recinto.ancho_m, 3)} × {fmt(recinto.fondo_m, 3)} × {fmt(recinto.altura_m, 3)}",
        v, "m³",
        origen="Simulación matemática!N13",
    )
    return v


def metodo_estandar(
    recinto: Recinto,
    artefactos: Sequence[Artefacto],
    parametros: Parametros,
    bitacora: Bitacora,
) -> ResultadoEstandar:
    """Evalúa si el volumen del recinto alcanza 3,4 m³ por kW de potencia agregada."""
    p, excluida = potencia_total(artefactos, bitacora)
    v = volumen(recinto, bitacora)

    v_util = v
    if parametros.restar_margen_muebles:
        v_util = v * (1 - parametros.margen_muebles)
        bitacora.paso(
            "Volumen útil tras restar muebles y enseres (recomendación, no es de la norma)",
            "V útil = V × (1 − margen)",
            f"{fmt(v, 3)} × (1 − {fmt(parametros.margen_muebles)})",
            v_util, "m³",
            origen="4.1.1 Método estándar!I40",
        )
        bitacora.advertir(
            Nivel.INFO,
            f"Se restó el {fmt(parametros.margen_muebles * 100, 0)} % del volumen por "
            "muebles. Es una recomendación del instructor; la norma no lo exige.",
        )

    k = bitacora.constante(VOLUMEN_POR_KW)
    v_requerido = k * p
    bitacora.paso(
        "Volumen requerido",
        "V req = 3,4 × P",
        f"{fmt(k)} × {fmt(p)}",
        v_requerido, "m³",
        numeral="4.1.1",
    )
    p_max = v_util / k
    bitacora.paso(
        "Potencia máxima que admite el recinto",
        "P máx = V ÷ 3,4",
        f"{fmt(v_util, 3)} ÷ {fmt(k)}",
        p_max, "kW",
        numeral="4.1.1",
    )

    if p == 0:
        bitacora.advertir(
            Nivel.INFO,
            "Todos los artefactos son de cámara estanca (Tipo C): el recinto no "
            "necesita ventilación por la NTC 3631.",
            "4.1.1, nota",
        )
        veredicto = f"{CUMPLE}: solo hay artefactos Tipo C"
        bitacora.paso("Veredicto", "P = 0", "Sin potencia que contar", veredicto, "",
                      numeral="4.1.1")
        return ResultadoEstandar(
            potencia_total_kw=0.0, potencia_excluida_kw=excluida, volumen_m3=v,
            volumen_util_m3=v_util, volumen_requerido_m3=0.0, potencia_maxima_kw=p_max,
            relacion_m3_kw=None, cumple=True, veredicto=veredicto, numeral="4.1.1",
        )

    relacion = v_util / p
    bitacora.paso(
        "Relación volumen ÷ potencia",
        "V ÷ P",
        f"{fmt(v_util, 3)} ÷ {fmt(p)}",
        relacion, "m³/kW",
        numeral="4.1.1",
        origen="Simulación matemática!O13",
    )
    cumple = relacion >= k
    veredicto = CUMPLE if cumple else NO_CUMPLE
    bitacora.paso(
        "Veredicto del método estándar",
        "V ÷ P ≥ 3,4",
        f"{fmt(relacion)} {'≥' if cumple else '<'} {fmt(k)}",
        veredicto, "",
        numeral="4.1.1",
        origen="Simulación matemática!Q13",
    )
    if not cumple:
        bitacora.advertir(
            Nivel.ADVERTENCIA,
            "El recinto no cumple el método estándar: debe ventilarse por uno de los "
            "métodos de los numerales 4.1.2 a 4.4.",
            "4.1.1",
        )
    return ResultadoEstandar(
        potencia_total_kw=p, potencia_excluida_kw=excluida, volumen_m3=v,
        volumen_util_m3=v_util, volumen_requerido_m3=v_requerido, potencia_maxima_kw=p_max,
        relacion_m3_kw=relacion, cumple=cumple, veredicto=veredicto, numeral="4.1.1",
    )


def hay_artefactos_tipo(artefactos: Sequence[Artefacto], tipo: TipoArtefacto) -> bool:
    return any(a.tipo is tipo for a in artefactos)
