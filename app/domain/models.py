"""Modelos del dominio de ventilación según NTC 3631."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Circuito(StrEnum):
    """Circuito de combustión del artefacto.

    Los artefactos de circuito estanco (Tipo C) no consumen aire del recinto y la
    norma los excluye de la potencia agregada (numeral 4.1.1, nota).
    """

    ABIERTO = "abierto"
    ESTANCO = "estanco"


class TipoRecinto(StrEnum):
    COCINA = "cocina"
    DORMITORIO = "dormitorio"
    BANO = "bano"
    MONOESPACIAL = "monoespacial"
    COMERCIAL = "comercial"
    INDUSTRIAL = "industrial"
    OTRO = "otro"


class Nivel(StrEnum):
    """Ubicación del recinto respecto al nivel del terreno."""

    SOBRE_PRIMER_SOTANO = "sobre_primer_sotano"
    PRIMER_SOTANO = "primer_sotano"
    BAJO_PRIMER_SOTANO = "bajo_primer_sotano"


class Veredicto(StrEnum):
    CUMPLE = "cumple"
    NO_CUMPLE = "no_cumple"
    NO_PERMITIDO = "no_permitido"


class Artefacto(BaseModel):
    """Un artefacto a gas instalado en el recinto."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1)
    potencia_kw: float = Field(gt=0, description="Potencia nominal declarada por el fabricante.")
    circuito: Circuito = Circuito.ABIERTO
    diametro_conector_cm: float | None = Field(
        default=None,
        gt=0,
        description="Diámetro del conector de evacuación. Necesario para el Método 2 (4.2.2).",
    )


class Recinto(BaseModel):
    """El espacio donde se instalan los artefactos."""

    model_config = ConfigDict(extra="forbid")

    ancho_m: float = Field(gt=0)
    fondo_m: float = Field(gt=0)
    alto_m: float = Field(gt=0)
    tipo: TipoRecinto = TipoRecinto.COCINA
    nivel: Nivel = Nivel.SOBRE_PRIMER_SOTANO
    altitud_msnm: float = Field(default=1000.0, ge=0)
    densidad_gas_relativa: float = Field(
        default=0.6,
        gt=0,
        description="Densidad del gas respecto al aire. El gas natural ronda 0,6.",
    )
    volumen_comunicado_m3: float = Field(
        default=0.0,
        ge=0,
        description="Volumen adicional de espacios interiores comunicados de forma permanente.",
    )

    @property
    def volumen_bruto_m3(self) -> float:
        return self.ancho_m * self.fondo_m * self.alto_m


class Opciones(BaseModel):
    """Decisiones de cálculo que no son de la norma y deben declararse en el informe."""

    model_config = ConfigDict(extra="forbid")

    aplicar_margen_muebles: bool = Field(
        default=False,
        description="Descuenta 20 % del volumen. Recomendación del instructor, no de la norma.",
    )


class Paso(BaseModel):
    """Un renglón de la traza de cálculo. Sin esto el veredicto no es auditable."""

    numeral: str
    titulo: str
    detalle: str
    valor: str | None = None


class Resultado(BaseModel):
    """Lo que devuelve el motor. Es la interfaz con la API y con el informe."""

    veredicto: Veredicto
    metodo: str
    numeral: str
    resumen: str

    volumen_m3: float
    volumen_efectivo_m3: float
    potencia_agregada_kw: float
    potencia_excluida_kw: float
    volumen_requerido_m3: float
    relacion_m3_kw: float | None

    pasos: list[Paso] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
