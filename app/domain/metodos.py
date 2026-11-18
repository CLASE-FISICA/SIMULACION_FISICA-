"""Dimensionamiento de los métodos alternos de ventilación (BE-03 y BE-04).

Cada método se resuelve en dos pasos:
1. el área libre que exige la norma para cada abertura, y
2. la geometría que la materializa: rejilla, conducto vertical u horizontal.
Así la combinación del numeral 4.3 reutiliza el paso 2 del método exterior
con el área reducida.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field, replace

from app.domain.bitacora import Bitacora, fmt
from app.domain.catalogos import (
    CONDUCTOS_PROVISIONALES,
    REJILLAS_PROVISIONALES,
    VENTILADORES_PROVISIONALES,
    redondear_a_multiplo,
    seleccionar_conducto,
    seleccionar_rejilla,
    seleccionar_ventilador,
)
from app.domain.modelos import (
    NOMBRE_METODO,
    NUMERAL_METODO,
    Artefacto,
    Conducto,
    ErrorDominio,
    Geometria,
    Metodo,
    Nivel,
    OpcionesMetodo,
    Rejilla,
    ResultadoDimensionamiento,
    TipoArtefacto,
    Ventilador,
)
from app.domain.normativa import (
    ALTITUD_MAXIMA_ANEXO_D,
    ALTURA_MAX_ABERTURA_INFERIOR,
    ALTURA_MIN_ABERTURA_SUPERIOR,
    AREA_ANEXO_D_POR_KW,
    AREA_DIFERENTES_PISOS_POR_KW,
    AREA_M1_DIRECTA_POR_KW,
    AREA_M1_HORIZONTAL_POR_KW,
    AREA_M1_VERTICAL_POR_KW,
    AREA_M2_POR_KW,
    AREA_MINIMA_ABERTURA,
    AREA_MISMO_PISO_MINIMA,
    AREA_MISMO_PISO_POR_KW,
    CAUDAL_MECANICO_POR_KW,
    DIMENSION_MINIMA_ABERTURA,
    SEPARACION_M2_FRONTAL,
    SEPARACION_M2_LATERAL_POSTERIOR,
    VOLUMEN_POR_KW,
    Constante,
    Parametros,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Catalogos:
    """Catálogos comerciales que usa el motor; la API los toma de la base."""

    rejillas: tuple[Rejilla, ...] = REJILLAS_PROVISIONALES
    conductos: tuple[Conducto, ...] = CONDUCTOS_PROVISIONALES
    ventiladores: tuple[Ventilador, ...] = VENTILADORES_PROVISIONALES


@dataclass(frozen=True, slots=True, kw_only=True)
class DatosCalculo:
    """Lo que necesita un método además de la bitácora."""

    potencia_kw: float
    volumen_util_m3: float
    artefactos: tuple[Artefacto, ...]
    opciones: OpcionesMetodo = field(default_factory=OpcionesMetodo)
    parametros: Parametros = field(default_factory=Parametros)
    catalogos: Catalogos = field(default_factory=Catalogos)


_SUPERIOR = (
    f"Superior: comienza a no menos de {fmt(ALTURA_MIN_ABERTURA_SUPERIOR.valor)} cm "
    "del piso"
)
_INFERIOR = (
    f"Inferior: comienza a no más de {fmt(ALTURA_MAX_ABERTURA_INFERIOR.valor)} cm "
    "del piso"
)

_ABERTURAS: dict[Metodo, tuple[int, tuple[str, ...]]] = {
    Metodo.MISMO_PISO: (2, (_SUPERIOR, _INFERIOR)),
    Metodo.DIFERENTES_PISOS: (1, ("Una o más aberturas en puertas o pisos que "
                                  "comunican los espacios",)),
    Metodo.M1_DIRECTA: (2, (_SUPERIOR, _INFERIOR)),
    Metodo.M1_CONDUCTO_VERTICAL: (2, (f"{_SUPERIOR}, conectada a un conducto vertical",
                                      f"{_INFERIOR}, conectada a un conducto vertical")),
    Metodo.M1_CONDUCTO_HORIZONTAL: (2, (f"{_SUPERIOR}, conectada a un conducto horizontal",
                                        f"{_INFERIOR}, conectada a un conducto horizontal")),
    Metodo.M2_UNA_ABERTURA: (1, (_SUPERIOR,)),
    Metodo.ANEXO_D: (1, ("Una abertura ubicada a más de 1 m del nivel del piso "
                         "(Simulación matemática!O64; texto del Anexo D por transcribir)",)),
}

_POR_KW: dict[Metodo, Constante] = {
    Metodo.DIFERENTES_PISOS: AREA_DIFERENTES_PISOS_POR_KW,
    Metodo.M1_DIRECTA: AREA_M1_DIRECTA_POR_KW,
    Metodo.M1_CONDUCTO_VERTICAL: AREA_M1_VERTICAL_POR_KW,
    Metodo.M1_CONDUCTO_HORIZONTAL: AREA_M1_HORIZONTAL_POR_KW,
    Metodo.ANEXO_D: AREA_ANEXO_D_POR_KW,
}

_ORIGEN_AREA: dict[Metodo, str] = {
    Metodo.MISMO_PISO: "Simulación matemática!G33, H33",
    Metodo.DIFERENTES_PISOS: "Simulación matemática!G39",
    Metodo.M1_DIRECTA: "Simulación matemática!G44",
    Metodo.M1_CONDUCTO_VERTICAL: "Simulación matemática!G49",
    Metodo.M1_CONDUCTO_HORIZONTAL: "Simulación matemática!G54",
    Metodo.M2_UNA_ABERTURA: "Simulación matemática!G59",
    Metodo.ANEXO_D: "Simulación matemática!G64",
}


# --- Paso 1: área libre que exige la norma ---------------------------------


def area_libre(metodo: Metodo, datos: DatosCalculo, b: Bitacora) -> float:
    """Área libre de cada abertura, en cm², según el método."""
    p = datos.potencia_kw
    numeral = NUMERAL_METODO[metodo]
    origen = _ORIGEN_AREA.get(metodo)

    if metodo is Metodo.MISMO_PISO:
        k = b.constante(AREA_MISMO_PISO_POR_KW)
        minimo = b.constante(AREA_MISMO_PISO_MINIMA)
        calculada = k * p
        b.paso("Área por potencia", "A = 22 × P", f"{fmt(k)} × {fmt(p)}", calculada, "cm²",
               numeral=numeral, origen="Simulación matemática!G33")
        area = max(calculada, minimo)
        b.paso("Área libre de cada abertura: el mayor entre 22 × P y 645 cm²",
               "A libre = máx(22 × P; 645)", f"máx({fmt(calculada)}; {fmt(minimo)})",
               area, "cm²", numeral=numeral, origen="Simulación matemática!H33")
        return area

    if metodo is Metodo.M2_UNA_ABERTURA:
        return _area_metodo_2(datos, b)

    k = b.constante(_POR_KW[metodo])
    area = k * p
    b.paso(f"Área libre de cada abertura ({NOMBRE_METODO[metodo]})",
           f"A libre = {fmt(k)} × P", f"{fmt(k)} × {fmt(p)}", area, "cm²",
           numeral=numeral, origen=origen)
    return area


def _area_metodo_2(datos: DatosCalculo, b: Bitacora) -> float:
    """Método 2: el mayor entre 11 cm²/kW y la suma de las áreas de los conectores."""
    p = datos.potencia_kw
    k = b.constante(AREA_M2_POR_KW)
    por_potencia = k * p
    b.paso("Área por potencia", "A = 11 × P", f"{fmt(k)} × {fmt(p)}", por_potencia, "cm²",
           numeral="4.2.2", origen="Simulación matemática!G59")

    areas: list[float] = []
    for a in datos.artefactos:
        if not a.cuenta_en_potencia:
            continue
        if a.diametro_conector_cm is None:
            if a.tipo is TipoArtefacto.B:
                b.advertir(
                    Nivel.ADVERTENCIA,
                    f"Falta el diámetro del conector de «{a.nombre}» (Tipo B): el área "
                    "del Método 2 debe compararse con la suma de las áreas de los conectores.",
                    "4.2.2",
                )
            continue
        area_conector = math.pi * a.diametro_conector_cm**2 / 4
        b.paso(f"Área del conector de «{a.nombre}»", "A = π × d² ÷ 4",
               f"π × {fmt(a.diametro_conector_cm)}² ÷ 4", area_conector, "cm²",
               numeral="4.2.2")
        areas.append(area_conector)

    suma = sum(areas)
    if areas:
        b.paso("Suma de las áreas de los conectores", "Σ A conectores",
               " + ".join(fmt(x) for x in areas), suma, "cm²", numeral="4.2.2")
    area = max(por_potencia, suma)
    b.paso("Área libre de la abertura: el mayor entre 11 × P y la suma de conectores",
           "A libre = máx(11 × P; Σ A conectores)", f"máx({fmt(por_potencia)}; {fmt(suma)})",
           area, "cm²", numeral="4.2.2")
    _verificar_separaciones(datos.artefactos, b)
    return area


def _verificar_separaciones(artefactos: Sequence[Artefacto], b: Bitacora) -> None:
    lat = SEPARACION_M2_LATERAL_POSTERIOR.valor
    frente = SEPARACION_M2_FRONTAL.valor
    faltan: list[str] = []
    for a in artefactos:
        if not a.cuenta_en_potencia:
            continue
        medidas = {
            "lateral": (a.separacion_lateral_cm, lat),
            "posterior": (a.separacion_posterior_cm, lat),
            "frontal": (a.separacion_frontal_cm, frente),
        }
        if any(valor is None for valor, _ in medidas.values()):
            faltan.append(a.nombre)
        for lado, (valor, minimo) in medidas.items():
            if valor is not None and valor < minimo:
                b.advertir(
                    Nivel.BLOQUEANTE,
                    f"«{a.nombre}» tiene {fmt(valor)} cm de separación {lado}; el Método 2 "
                    f"exige al menos {fmt(minimo)} cm. Use otro método.",
                    "4.2.2",
                )
    if faltan:
        b.advertir(
            Nivel.ADVERTENCIA,
            f"Verifique que {', '.join(f'«{n}»' for n in faltan)} tenga al menos "
            f"{fmt(lat)} cm de separación a los lados y atrás y {fmt(frente)} cm al frente; "
            "es requisito del Método 2.",
            "4.2.2",
        )


# --- Paso 2: geometría que materializa el área -----------------------------


def _aplicar_minimo(area: float, numeral: str, b: Bitacora) -> float:
    minimo = AREA_MINIMA_ABERTURA.valor
    if area >= minimo:
        return area
    b.paso("Se aplica el área mínima de una abertura (dimensión menor de 8 cm)",
           "A libre = máx(A; 64)", f"máx({fmt(area)}; {fmt(minimo)})", minimo, "cm²",
           numeral=AREA_MINIMA_ABERTURA.numeral, origen=AREA_MINIMA_ABERTURA.origen)
    b.advertir(
        Nivel.INFO,
        f"El área calculada ({fmt(area)} cm²) es menor que la de una abertura de "
        f"{fmt(DIMENSION_MINIMA_ABERTURA.valor)} cm × {fmt(DIMENSION_MINIMA_ABERTURA.valor)} cm; "
        f"se toma {fmt(minimo)} cm².",
        numeral,
    )
    return minimo


def geometria(
    metodo: Metodo, libre: float, datos: DatosCalculo, b: Bitacora
) -> ResultadoDimensionamiento:
    """Convierte el área libre de cada abertura en rejilla o conducto comercial."""
    numeral = NUMERAL_METODO[metodo]
    numero, ubicacion = _ABERTURAS[metodo]
    libre = _aplicar_minimo(libre, numeral, b)
    base = ResultadoDimensionamiento(
        metodo=metodo, nombre_metodo=NOMBRE_METODO[metodo], numeral=numeral,
        numero_aberturas=numero, ubicacion=ubicacion, area_libre_cm2=libre,
    )
    if metodo is Metodo.M1_CONDUCTO_VERTICAL:
        return _conducto_vertical(base, libre, datos, b)
    if metodo is Metodo.M1_CONDUCTO_HORIZONTAL:
        return _conducto_horizontal(base, libre, datos, b)
    return _rejilla(base, libre, datos, b)


def _area_bruta(libre: float, factor: float, descripcion: str, origen: str,
                b: Bitacora) -> float:
    total = libre / factor
    b.paso(descripcion, "A total = A libre ÷ factor", f"{fmt(libre)} ÷ {fmt(factor)}",
           total, "cm²", origen=origen)
    return total


def _rejilla(base: ResultadoDimensionamiento, libre: float, datos: DatosCalculo,
             b: Bitacora) -> ResultadoDimensionamiento:
    factor = datos.parametros.factor_rejilla
    total = _area_bruta(libre, factor,
                        "Área total de la rejilla (el material ocupa parte de la rejilla)",
                        "Simulación matemática!I33", b)
    lado = math.sqrt(total)
    b.paso("Lado de la rejilla cuadrada", "L = √A total", f"√{fmt(total)}", lado, "cm",
           origen="Simulación matemática!L33")
    rejilla = seleccionar_rejilla(libre, factor, datos.catalogos.rejillas)
    if rejilla is None:
        b.advertir(
            Nivel.ADVERTENCIA,
            f"Ninguna rejilla del catálogo da {fmt(libre)} cm² de área efectiva: use varias "
            "rejillas o una fabricada a medida.",
            base.numeral,
        )
    else:
        b.paso("Rejilla comercial: la menor del catálogo cuya área efectiva cumple",
               "A efectiva = ancho × alto × factor ≥ A libre",
               f"{fmt(rejilla.ancho_cm)} × {fmt(rejilla.alto_cm)} × {fmt(factor)} = "
               f"{fmt(rejilla.area_efectiva_cm2(factor))} ≥ {fmt(libre)}",
               rejilla.nombre, "cm", origen=rejilla.origen)
    return replace(base, area_total_cm2=total, geometria=Geometria.CUADRADA, lado_cm=lado,
                   rejilla_comercial=rejilla)


def _conducto_vertical(base: ResultadoDimensionamiento, libre: float, datos: DatosCalculo,
                       b: Bitacora) -> ResultadoDimensionamiento:
    params = datos.parametros
    if params.aplicar_factor_conducto_vertical:
        seccion = _area_bruta(libre, params.factor_conducto_vertical,
                              "Sección del conducto vertical (factor de diseño)",
                              "Simulación matemática!H49", b)
    else:
        seccion = libre
        b.paso("Sección del conducto igual al área libre de la abertura",
               "A conducto = A libre", fmt(libre), seccion, "cm²", numeral="4.2")
    diametro = math.sqrt(4 * seccion / math.pi)
    b.paso("Diámetro del conducto circular", "D = √(4 × A ÷ π)", f"√(4 × {fmt(seccion)} ÷ π)",
           diametro, "cm", origen="Simulación matemática!L49")
    b.paso("Diámetro en pulgadas", "D ÷ 2,54", f"{fmt(diametro)} ÷ 2,54", diametro / 2.54,
           "pulg", origen="Simulación matemática!M49")
    conducto = seleccionar_conducto(seccion, datos.catalogos.conductos)
    if conducto is None:
        b.advertir(Nivel.ADVERTENCIA,
                   f"Ningún conducto comercial del catálogo tiene {fmt(seccion)} cm² de sección.",
                   base.numeral)
    else:
        b.paso("Conducto comercial: el menor diámetro cuya sección cumple",
               "π × D² ÷ 4 ≥ A conducto",
               f"π × {fmt(conducto.diametro_cm)}² ÷ 4 = {fmt(conducto.area_cm2)} ≥ {fmt(seccion)}",
               conducto.diametro_pulg, "pulg")
    return replace(base, area_total_cm2=seccion, geometria=Geometria.CIRCULAR,
                   diametro_cm=diametro, conducto_comercial=conducto)


def _conducto_horizontal(base: ResultadoDimensionamiento, libre: float, datos: DatosCalculo,
                         b: Bitacora) -> ResultadoDimensionamiento:
    params = datos.parametros
    seccion = _area_bruta(libre, params.factor_rejilla,
                          "Sección del conducto horizontal (rejilla en la boca)",
                          "Simulación matemática!H54", b)
    lado = math.sqrt(seccion)
    b.paso("Lado del conducto cuadrado", "L = √A", f"√{fmt(seccion)}", lado, "cm",
           origen="Simulación matemática!L54")
    construible = redondear_a_multiplo(lado, params.paso_lado_construible_cm)
    b.paso(f"Lado construible: múltiplo de {fmt(params.paso_lado_construible_cm)} cm hacia arriba",
           "⌈L ÷ paso⌉ × paso", f"⌈{fmt(lado)} ÷ {fmt(params.paso_lado_construible_cm)}⌉ × "
           f"{fmt(params.paso_lado_construible_cm)}", construible, "cm",
           origen="Simulación matemática!M54")
    return replace(base, area_total_cm2=seccion, geometria=Geometria.CUADRADA, lado_cm=lado,
                   lado_construible_cm=construible)


# --- Métodos completos -----------------------------------------------------


def _verificar_volumen_combinado(datos: DatosCalculo, b: Bitacora) -> None:
    """4.1.2: los espacios comunicados deben sumar el volumen del método estándar."""
    comunicado = datos.opciones.volumen_espacios_comunicados_m3
    if comunicado is None:
        b.advertir(
            Nivel.ADVERTENCIA,
            "Confirme que el volumen del recinto más el de los espacios comunicados alcance "
            f"{fmt(VOLUMEN_POR_KW.valor)} m³/kW; si no alcanza, use la combinación de aire "
            "interior y exterior (4.3).",
            "4.1.2",
        )
        return
    total = datos.volumen_util_m3 + comunicado
    b.paso("Volumen de los espacios comunicados", "V total = V recinto + V comunicado",
           f"{fmt(datos.volumen_util_m3, 3)} + {fmt(comunicado, 3)}", total, "m³",
           numeral="4.1.2")
    relacion = total / datos.potencia_kw
    cumple = relacion >= VOLUMEN_POR_KW.valor
    b.paso("Relación del volumen combinado", "V total ÷ P ≥ 3,4",
           f"{fmt(relacion)} {'≥' if cumple else '<'} {fmt(VOLUMEN_POR_KW.valor)}",
           "Cumple" if cumple else "No cumple", "", numeral="4.1.2")
    if not cumple:
        b.advertir(
            Nivel.BLOQUEANTE,
            "El volumen combinado no alcanza el del método estándar: las aberturas interiores "
            "no bastan. Use la combinación de aire interior y exterior (4.3).",
            "4.1.2",
        )


def dimensionar_aberturas(metodo: Metodo, datos: DatosCalculo,
                          b: Bitacora) -> ResultadoDimensionamiento:
    """Métodos que se resuelven con área libre + geometría."""
    if metodo in (Metodo.MISMO_PISO, Metodo.DIFERENTES_PISOS):
        _verificar_volumen_combinado(datos, b)
    if metodo is Metodo.ANEXO_D:
        _verificar_altitud(datos.opciones.altitud_msnm, b)
    return geometria(metodo, area_libre(metodo, datos, b), datos, b)


def _verificar_altitud(altitud: float | None, b: Bitacora) -> None:
    limite = ALTITUD_MAXIMA_ANEXO_D.valor
    if altitud is None:
        b.advertir(Nivel.ADVERTENCIA,
                   f"Confirme que el recinto está a menos de {fmt(limite)} msnm; el Anexo D "
                   "solo aplica por debajo de esa altitud.", "Anexo D")
    elif altitud >= limite:
        b.advertir(Nivel.BLOQUEANTE,
                   f"El recinto está a {fmt(altitud)} msnm: el Anexo D solo aplica por debajo "
                   f"de {fmt(limite)} msnm.", "Anexo D")


def combinacion(datos: DatosCalculo, b: Bitacora) -> ResultadoDimensionamiento:
    """4.3: la abertura exterior del 4.2 se reduce según el aire que aporta el interior."""
    p = datos.potencia_kw
    comunicado = datos.opciones.volumen_espacios_comunicados_m3 or 0.0
    if comunicado <= 0:
        raise ErrorDominio("El método 4.3 requiere espacios interiores comunicados.")
    disponible = datos.volumen_util_m3 + comunicado
    b.paso("Volumen disponible de todos los espacios comunicados",
           "V disp = V recinto + V comunicado",
           f"{fmt(datos.volumen_util_m3, 3)} + {fmt(comunicado, 3)}", disponible, "m³",
           numeral="4.3 c) a)", origen="4.3 Comb de aire int y ext!E78")
    k = b.constante(VOLUMEN_POR_KW)
    requerido = k * p
    b.paso("Volumen requerido", "V req = 3,4 × P", f"{fmt(k)} × {fmt(p)}", requerido, "m³",
           numeral="4.3 c) a)", origen="4.3 Comb de aire int y ext!J78")
    relacion = disponible / requerido
    b.paso("Relación de espacio interior", "R = V disp ÷ V req",
           f"{fmt(disponible, 3)} ÷ {fmt(requerido, 3)}", relacion, "adim.",
           numeral="4.3 c) a)", origen="4.3 Comb de aire int y ext!J83")
    if relacion >= 1:
        raise ErrorDominio(
            "El volumen disponible ya alcanza el requerido: no hace falta la "
            "abertura exterior del método 4.3; evalúe el numeral 4.1.2."
        )
    factor = max(0.0, 1 - relacion)
    b.paso("Factor de reducción del tamaño exterior", "F = 1 − R", f"1 − {fmt(relacion, 4)}",
           factor, "adim.", numeral="4.3 c) b)", origen="4.3 Comb de aire int y ext!J85")

    exterior = datos.opciones.metodo_exterior_combinacion
    area_42 = area_libre(exterior, datos, b)
    reducida = area_42 * factor
    b.paso(f"Área de la abertura exterior ({NOMBRE_METODO[exterior]} × factor)",
           "A ext = A 4.2 × F", f"{fmt(area_42)} × {fmt(factor, 4)}", reducida, "cm²",
           numeral="4.3 c) c)", origen="4.3 Comb de aire int y ext!F104")
    resultado_exterior = geometria(exterior, reducida, datos, b)

    interiores = None
    if comunicado > 0:
        metodo_int = (Metodo.DIFERENTES_PISOS if datos.opciones.interiores_en_diferentes_pisos
                      else Metodo.MISMO_PISO)
        b.paso("Aberturas interiores hacia los espacios comunicados", "Numeral 4.1.2",
               NOMBRE_METODO[metodo_int], NUMERAL_METODO[metodo_int], "", numeral="4.3 a)")
        interiores = geometria(metodo_int, area_libre(metodo_int, datos, b), datos, b)

    return replace(
        resultado_exterior,
        metodo=Metodo.COMBINACION,
        nombre_metodo=f"{NOMBRE_METODO[Metodo.COMBINACION]} (exterior por "
                      f"{NOMBRE_METODO[exterior]})",
        numeral=f"4.3 y {NUMERAL_METODO[exterior]}",
        factor_reduccion=factor,
        aberturas_interiores=interiores,
    )


def suministro_mecanico(datos: DatosCalculo, b: Bitacora) -> ResultadoDimensionamiento:
    """4.4: caudal de aire exterior de 0,034 m³/min por kW, más la extracción a reponer."""
    p = datos.potencia_kw
    k = b.constante(CAUDAL_MECANICO_POR_KW)
    q_min = k * p
    b.paso("Caudal de aire de combustión", "Q = 0,034 × P", f"{fmt(k, 3)} × {fmt(p)}", q_min,
           "m³/min", numeral="4.4", origen="Simulación matemática!G69")
    q_h = q_min * 60
    b.paso("Caudal de aire de combustión por hora", "Q × 60", f"{fmt(q_min, 3)} × 60", q_h,
           "m³/h", numeral="4.4", origen="Simulación matemática!H69")
    extraccion = datos.opciones.extraccion_cocina_m3h
    total = q_h + extraccion
    b.paso("Caudal total: aire de combustión más reposición de la extracción",
           "Q total = Q + Q extracción", f"{fmt(q_h)} + {fmt(extraccion)}", total, "m³/h",
           origen="Simulación matemática!M69")
    ventilador = seleccionar_ventilador(total, datos.catalogos.ventiladores)
    if ventilador is None:
        b.advertir(Nivel.ADVERTENCIA,
                   f"Ningún ventilador del catálogo entrega {fmt(total)} m³/h.", "4.4")
    else:
        b.paso("Ventilador: la menor capacidad que cubre el suministro total",
               "Q ventilador ≥ Q total", f"{fmt(ventilador.capacidad_m3h)} ≥ {fmt(total)}",
               ventilador.capacidad_m3h, "m³/h", origen="Simulación matemática!J69")
    b.advertir(Nivel.INFO,
               "El suministro mecánico debe enclavarse con los artefactos: si el ventilador "
               "se detiene, los artefactos deben apagarse.", "4.4")
    if extraccion == 0:
        b.advertir(Nivel.INFO,
                   "No se indicó extracción: si el recinto tiene campana o extractor, su "
                   "caudal debe reponerse y sumarse al aire de combustión.", "4.4")
    return ResultadoDimensionamiento(
        metodo=Metodo.SUMINISTRO_MECANICO, nombre_metodo=NOMBRE_METODO[Metodo.SUMINISTRO_MECANICO],
        numeral="4.4", numero_aberturas=0, ubicacion=(),
        caudal_combustion_m3h=q_h, caudal_total_m3h=total, ventilador=ventilador,
    )


def dimensionar(metodo: Metodo, datos: DatosCalculo, b: Bitacora) -> ResultadoDimensionamiento:
    if metodo is Metodo.ESTANDAR:
        raise ErrorDominio("El método estándar no se dimensiona: se evalúa con el volumen.")
    if datos.potencia_kw <= 0:
        raise ErrorDominio("No hay potencia que ventilar: todos los artefactos son Tipo C.")
    b.paso("Método de ventilación elegido", "—", NOMBRE_METODO[metodo], NUMERAL_METODO[metodo],
           "", numeral=NUMERAL_METODO[metodo])
    if metodo is Metodo.COMBINACION:
        return combinacion(datos, b)
    if metodo is Metodo.SUMINISTRO_MECANICO:
        return suministro_mecanico(datos, b)
    return dimensionar_aberturas(metodo, datos, b)