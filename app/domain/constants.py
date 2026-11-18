"""Constantes normativas de la NTC 3631, con su numeral y su unidad.

Regla del proyecto (ADR-002): las constantes viven en el código, tipadas y con su
numeral, nunca en la base de datos. La base puede guardar una copia para consulta,
pero el motor calcula siempre con estas. Una prueba verifica que la copia coincide.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Constante(BaseModel):
    """Un valor normativo con su procedencia."""

    model_config = ConfigDict(frozen=True)

    clave: str
    valor: float
    unidad: str
    numeral: str
    descripcion: str


# --- Numeral 4.1: todo el aire proviene del interior -------------------------

VOLUMEN_MINIMO_POR_KW = Constante(
    clave="volumen_minimo_por_kw",
    valor=3.4,
    unidad="m3/kW",
    numeral="4.1.1",
    descripcion="Volumen mínimo del recinto por kW de potencia nominal agregada.",
)

AREA_MISMO_PISO_CM2_KW = Constante(
    clave="area_mismo_piso_cm2_kw",
    valor=22.0,
    unidad="cm2/kW",
    numeral="4.1.2 a)",
    descripcion="Área libre por kW de cada una de las dos aberturas interiores, mismo piso.",
)

AREA_MISMO_PISO_MIN_CM2 = Constante(
    clave="area_mismo_piso_min_cm2",
    valor=645.0,
    unidad="cm2",
    numeral="4.1.2 a)",
    descripcion="Área libre mínima absoluta por abertura interior en el mismo piso.",
)

AREA_DISTINTO_PISO_CM2_KW = Constante(
    clave="area_distinto_piso_cm2_kw",
    valor=44.0,
    unidad="cm2/kW",
    numeral="4.1.2 b)",
    descripcion="Área libre por kW de las aberturas que comunican espacios en distintos pisos.",
)

# --- Numeral 4.2: todo el aire proviene del exterior ------------------------

AREA_DIRECTO_CM2_KW = Constante(
    clave="area_directo_cm2_kw",
    valor=6.0,
    unidad="cm2/kW",
    numeral="4.2.1 a)",
    descripcion="Área libre por kW de cada abertura con comunicación directa o conducto vertical.",
)

AREA_CONDUCTO_HORIZONTAL_CM2_KW = Constante(
    clave="area_conducto_horizontal_cm2_kw",
    valor=11.0,
    unidad="cm2/kW",
    numeral="4.2.1 b)",
    descripcion="Área libre por kW de cada abertura comunicada mediante conducto horizontal.",
)

AREA_METODO_2_CM2_KW = Constante(
    clave="area_metodo_2_cm2_kw",
    valor=11.0,
    unidad="cm2/kW",
    numeral="4.2.2",
    descripcion=(
        "Área libre por kW de la única abertura permanente. Se compara con la suma de "
        "las áreas de los conectores y rige el mayor de los dos."
    ),
)

ALTITUD_ANEXO_D_MSNM = Constante(
    clave="altitud_anexo_d_msnm",
    valor=260.0,
    unidad="msnm",
    numeral="Anexo D",
    descripcion="Por debajo de esta altitud aplica el Anexo D con su propio criterio de área.",
)

AREA_ANEXO_D_CM2_KW = Constante(
    clave="area_anexo_d_cm2_kw",
    valor=150.0,
    unidad="cm2/kW",
    numeral="Anexo D.1.1",
    descripcion="Área libre por kW para recintos situados a menos de 260 msnm.",
)

# --- Numeral 4.4: suministro mecánico --------------------------------------

CAUDAL_MECANICO_M3_MIN_KW = Constante(
    clave="caudal_mecanico_m3_min_kw",
    valor=0.034,
    unidad="m3/(min*kW)",
    numeral="4.4",
    descripcion="Caudal mínimo de aire de combustión por kW cuando el suministro es mecánico.",
)

# --- Reglas transversales --------------------------------------------------

DIMENSION_MINIMA_ABERTURA_CM = Constante(
    clave="dimension_minima_abertura_cm",
    valor=8.0,
    unidad="cm",
    numeral="4.1.2 y 4.2",
    descripcion=(
        "Ninguna abertura de ventilación puede tener una dimensión menor a 8 cm. "
        "Es un mínimo absoluto: se aplica por encima de cualquier cálculo por potencia."
    ),
)

FACTOR_OBTURACION_REJILLA = Constante(
    clave="factor_obturacion_rejilla",
    valor=0.60,
    unidad="adimensional",
    numeral="práctica de diseño",
    descripcion=(
        "Fracción de área libre de una rejilla; el 40 % restante lo ocupa el material. "
        "No es texto de la norma: es configurable y debe declararse en el informe."
    ),
)

MARGEN_MUEBLES = Constante(
    clave="margen_muebles",
    valor=0.20,
    unidad="adimensional",
    numeral="recomendación del instructor",
    descripcion=(
        "Descuento de volumen por muebles y enseres. No está en la norma y viene "
        "desactivado por defecto; si se activa, el informe debe decirlo."
    ),
)


NORMATIVA: dict[str, Constante] = {
    c.clave: c
    for c in (
        VOLUMEN_MINIMO_POR_KW,
        AREA_MISMO_PISO_CM2_KW,
        AREA_MISMO_PISO_MIN_CM2,
        AREA_DISTINTO_PISO_CM2_KW,
        AREA_DIRECTO_CM2_KW,
        AREA_CONDUCTO_HORIZONTAL_CM2_KW,
        AREA_METODO_2_CM2_KW,
        ALTITUD_ANEXO_D_MSNM,
        AREA_ANEXO_D_CM2_KW,
        CAUDAL_MECANICO_M3_MIN_KW,
        DIMENSION_MINIMA_ABERTURA_CM,
        FACTOR_OBTURACION_REJILLA,
        MARGEN_MUEBLES,
    )
}


def area_minima_abertura_cm2() -> float:
    """Área libre mínima que implica la dimensión mínima de 8 cm.

    Una abertura cuadrada de 8 cm de lado tiene 64 cm². Se calcula, no se escribe:
    si mañana cambia la dimensión mínima, el área cambia sola.
    """
    lado = DIMENSION_MINIMA_ABERTURA_CM.valor
    return lado * lado
