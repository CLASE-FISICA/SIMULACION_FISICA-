"""Constantes normativas de la NTC 3631 y parámetros de diseño configurables.

Cada constante lleva el numeral de la norma que la respalda y la celda del
Excel «Simulación matemática aplicada a ventilación NTC 3631» de donde se tomó.
Un cambio de cualquier valor es una versión nueva del motor (ver BE-15).
"""

from dataclasses import dataclass

VERSION_NORMA = "NTC 3631 (edición por confirmar con el instructor)"
VERSION_MOTOR = "0.1.0"

AVISO_NO_CERTIFICA = (
    "Esta herramienta es un recurso pedagógico: verifica los requisitos de "
    "ventilación de la NTC 3631, pero no certifica instalaciones."
)


@dataclass(frozen=True, slots=True)
class Constante:
    """Valor normativo trazable a su numeral y a su celda de origen."""

    clave: str
    valor: float
    unidad: str
    numeral: str
    origen: str
    descripcion: str
    es_norma: bool = True
    """False cuando es práctica de diseño o recomendación del instructor."""


# --- 4.1.1 Método estándar -------------------------------------------------
VOLUMEN_POR_KW = Constante(
    "volumen_por_kw", 3.4, "m³/kW", "4.1.1", "Simulación matemática!P13",
    "Volumen mínimo del recinto por cada kW de potencia nominal agregada",
)

# --- 4.1.2 Aberturas en el interior ----------------------------------------
AREA_MISMO_PISO_POR_KW = Constante(
    "area_mismo_piso_por_kw", 22.0, "cm²/kW", "4.1.2 a)", "Simulación matemática!D33",
    "Área libre de cada abertura interior, espacios en el mismo piso",
)
AREA_MISMO_PISO_MINIMA = Constante(
    "area_mismo_piso_minima", 645.0, "cm²", "4.1.2 a)", "Simulación matemática!D34",
    "Área libre mínima de cada abertura interior, espacios en el mismo piso",
)
AREA_DIFERENTES_PISOS_POR_KW = Constante(
    "area_diferentes_pisos_por_kw", 44.0, "cm²/kW", "4.1.2 b)",
    "Simulación matemática!D39",
    "Área libre de la abertura entre espacios en diferentes pisos",
)

# --- 4.2 Todo el aire proviene del exterior --------------------------------
AREA_M1_DIRECTA_POR_KW = Constante(
    "area_m1_directa_por_kw", 6.0, "cm²/kW", "4.2.1 a)", "Simulación matemática!D44",
    "Área libre de cada abertura, comunicación directa con el exterior",
)
AREA_M1_VERTICAL_POR_KW = Constante(
    "area_m1_vertical_por_kw", 6.0, "cm²/kW", "4.2.1 a)", "Simulación matemática!D49",
    "Área libre de cada abertura, conductos verticales",
)
AREA_M1_HORIZONTAL_POR_KW = Constante(
    "area_m1_horizontal_por_kw", 11.0, "cm²/kW", "4.2.1 b)",
    "Simulación matemática!D54",
    "Área libre de cada abertura, conductos horizontales",
)
AREA_M2_POR_KW = Constante(
    "area_m2_por_kw", 11.0, "cm²/kW", "4.2.2", "Simulación matemática!D59",
    "Área libre de la abertura única del Método 2",
)
DIMENSION_MINIMA_ABERTURA = Constante(
    "dimension_minima_abertura", 8.0, "cm", "4.1.2 y 4.2",
    "Simulación matemática!K33, J44",
    "Dimensión menor de una abertura de ventilación",
)
AREA_MINIMA_ABERTURA = Constante(
    "area_minima_abertura", 64.0, "cm²", "4.2", "Simulación matemática!K44",
    "Área mínima de una abertura (8 cm × 8 cm)",
)
SEPARACION_M2_LATERAL_POSTERIOR = Constante(
    "separacion_m2_lateral_posterior", 2.5, "cm", "4.2.2", "4.2.2 Método 2!H21",
    "Separación mínima del artefacto a sus lados y en la parte posterior",
)
SEPARACION_M2_FRONTAL = Constante(
    "separacion_m2_frontal", 16.0, "cm", "4.2.2", "4.2.2 Método 2!H21",
    "Separación mínima al frente del artefacto",
)

# --- Ubicación de las aberturas -------------------------------------------
ALTURA_MIN_ABERTURA_SUPERIOR = Constante(
    "altura_min_abertura_superior", 180.0, "cm", "4.1.2 y 4.2.1",
    "4.1.1 Método estándar!D73",
    "La abertura superior comienza a no menos de esta altura del piso",
)
ALTURA_MAX_ABERTURA_INFERIOR = Constante(
    "altura_max_abertura_inferior", 30.0, "cm", "4.1.2 y 4.2.1",
    "4.1.1 Método estándar!D75",
    "La abertura inferior comienza a no más de esta altura del piso",
)

# --- Anexo D ---------------------------------------------------------------
AREA_ANEXO_D_POR_KW = Constante(
    "area_anexo_d_por_kw", 150.0, "cm²/kW", "Anexo D", "Simulación matemática!D64",
    "Área libre de la abertura en recintos a menos de 260 msnm",
)
ALTITUD_MAXIMA_ANEXO_D = Constante(
    "altitud_maxima_anexo_d", 260.0, "msnm", "Anexo D", "Anexo D recintos < 260 m!B2",
    "Altitud por debajo de la cual aplica el Anexo D",
)

# --- 4.4 Suministro mecánico -------------------------------------------------
CAUDAL_MECANICO_POR_KW = Constante(
    "caudal_mecanico_por_kw", 0.034, "m³/min·kW", "4.4", "Simulación matemática!D69",
    "Caudal de aire exterior por cada kW de potencia nominal agregada",
)

# --- Prácticas de diseño (no son texto de la norma) ------------------------
FACTOR_REJILLA = Constante(
    "factor_rejilla", 0.6, "adim.", "Práctica de diseño", "Simulación matemática!I33",
    "Fracción efectiva de una rejilla (el 40 % lo ocupa el material)",
    es_norma=False,
)
FACTOR_CONDUCTO_VERTICAL = Constante(
    "factor_conducto_vertical", 0.75, "adim.", "Práctica de diseño",
    "Simulación matemática!H49",
    "Fracción efectiva de la sección de un conducto vertical",
    es_norma=False,
)
MARGEN_MUEBLES = Constante(
    "margen_muebles", 0.20, "adim.", "Recomendación del instructor",
    "4.1.1 Método estándar!I40",
    "Fracción del volumen que se resta por muebles y enseres",
    es_norma=False,
)
PASO_LADO_CONSTRUIBLE = Constante(
    "paso_lado_construible", 5.0, "cm", "Práctica de diseño", "Simulación matemática!M54",
    "Múltiplo al que se redondea hacia arriba el lado de un conducto construido",
    es_norma=False,
)

# --- Conversión de unidades (Taller práctico, E9 a E17) --------------------
BTU_H_POR_KW = 3412.142
MJ_H_POR_KW = 3.6

CONSTANTES: tuple[Constante, ...] = (
    VOLUMEN_POR_KW,
    AREA_MISMO_PISO_POR_KW,
    AREA_MISMO_PISO_MINIMA,
    AREA_DIFERENTES_PISOS_POR_KW,
    AREA_M1_DIRECTA_POR_KW,
    AREA_M1_VERTICAL_POR_KW,
    AREA_M1_HORIZONTAL_POR_KW,
    AREA_M2_POR_KW,
    DIMENSION_MINIMA_ABERTURA,
    AREA_MINIMA_ABERTURA,
    SEPARACION_M2_LATERAL_POSTERIOR,
    SEPARACION_M2_FRONTAL,
    ALTURA_MIN_ABERTURA_SUPERIOR,
    ALTURA_MAX_ABERTURA_INFERIOR,
    AREA_ANEXO_D_POR_KW,
    ALTITUD_MAXIMA_ANEXO_D,
    CAUDAL_MECANICO_POR_KW,
    FACTOR_REJILLA,
    FACTOR_CONDUCTO_VERTICAL,
    MARGEN_MUEBLES,
    PASO_LADO_CONSTRUIBLE,
)
"""Todas las constantes, para que BD-05 compare la tabla de la base con el motor."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Parametros:
    """Parámetros de diseño que el instructor puede ajustar.

    Los valores por defecto reproducen el Excel. Se guardan junto con cada
    evaluación para que una simulación antigua no cambie de resultado.
    """

    factor_rejilla: float = FACTOR_REJILLA.valor
    factor_conducto_vertical: float = FACTOR_CONDUCTO_VERTICAL.valor
    aplicar_factor_conducto_vertical: bool = True
    """Decisión pendiente del instructor: con el factor el caso 4 pide 7", sin él 6"."""
    restar_margen_muebles: bool = False
    margen_muebles: float = MARGEN_MUEBLES.valor
    paso_lado_construible_cm: float = PASO_LADO_CONSTRUIBLE.valor

    def __post_init__(self) -> None:
        for nombre in ("factor_rejilla", "factor_conducto_vertical"):
            valor = getattr(self, nombre)
            if not 0 < valor <= 1:
                raise ValueError(f"{nombre} debe estar entre 0 y 1; se recibió {valor}")
        if not 0 <= self.margen_muebles < 1:
            raise ValueError("margen_muebles debe estar entre 0 y 1")
        if self.paso_lado_construible_cm <= 0:
            raise ValueError("paso_lado_construible_cm debe ser mayor que cero")
