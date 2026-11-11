"""Esquemas de la API.

Son copia del dominio, no el dominio (decisión D6 del ADR-003). Si expusiéramos los
modelos del motor, un cambio de BE1 alteraría el contrato sin que nadie lo decidiera.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VeredictoDTO = Literal["cumple", "no_cumple", "no_permitido"]


# --- Solicitud --------------------------------------------------------------


class ArtefactoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1)
    potencia_kw: float = Field(gt=0)
    circuito: Literal["abierto", "estanco"] = "abierto"
    diametro_conector_cm: float | None = Field(default=None, gt=0)


class RecintoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ancho_m: float = Field(gt=0)
    fondo_m: float = Field(gt=0)
    alto_m: float = Field(gt=0)
    tipo: Literal[
        "cocina", "dormitorio", "bano", "monoespacial", "comercial", "industrial", "otro"
    ] = "cocina"
    nivel: Literal["sobre_primer_sotano", "primer_sotano", "bajo_primer_sotano"] = (
        "sobre_primer_sotano"
    )
    altitud_msnm: float = Field(default=1000.0, ge=0)
    densidad_gas_relativa: float = Field(default=0.6, gt=0)
    volumen_comunicado_m3: float = Field(default=0.0, ge=0)


class OpcionesDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aplicar_margen_muebles: bool = False


class SolicitudEvaluacionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recinto: RecintoDTO
    artefactos: list[ArtefactoDTO] = Field(min_length=1)
    opciones: OpcionesDTO = Field(default_factory=OpcionesDTO)
    ficha_id: str | None = None


# --- Respuesta --------------------------------------------------------------


class PasoDTO(BaseModel):
    numeral: str
    titulo: str
    detalle: str
    valor: str | None = None


class RequerimientoDTO(BaseModel):
    """Abertura u obra exigida. Vacío en la v0: se llena en el sprint 4."""

    numeral: str
    descripcion: str
    area_libre_min_cm2: float | None = None
    cantidad: int | None = None
    ubicacion: str | None = None
    rejilla_sugerida: str | None = None
    elemento_sugerido: str | None = None
    cumple: bool | None = None
    nota: str | None = None


class ResultadoDTO(BaseModel):
    veredicto: VeredictoDTO
    metodo: str
    numeral: str
    resumen: str
    volumen_m3: float
    volumen_efectivo_m3: float
    potencia_agregada_kw: float
    potencia_excluida_kw: float
    volumen_requerido_m3: float
    relacion_m3_kw: float | None
    pasos: list[PasoDTO]
    requerimientos: list[RequerimientoDTO] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    norma_version: str
    motor_version: str
    generado_en: datetime


class EvaluacionGuardadaDTO(BaseModel):
    id: str
    creada_en: datetime
    ficha_id: str | None
    aprendiz_id: str
    entradas: SolicitudEvaluacionDTO
    resultado: ResultadoDTO


class PaginaEvaluacionesDTO(BaseModel):
    items: list[EvaluacionGuardadaDTO]
    total: int
    page: int
    size: int
    pages: int


# --- Catálogos --------------------------------------------------------------


class ConstanteDTO(BaseModel):
    clave: str
    valor: float
    unidad: str
    numeral: str
    descripcion: str
    estado_validacion: Literal["validado", "pendiente_instructor", "practica_de_diseno"] = (
        "validado"
    )


class NormativaDTO(BaseModel):
    constantes: list[ConstanteDTO]
    area_minima_abertura_cm2: float
    norma_version: str
    nota: str


class RejillaDTO(BaseModel):
    id: str
    nombre: str
    ancho_cm: float
    alto_cm: float
    area_total_cm2: float
    area_efectiva_cm2: float
    factor_obturacion: float = 0.6
    geometria: Literal["cuadrada", "rectangular", "circular"] = "cuadrada"
    proveedor: str | None = None


class ListaRejillasDTO(BaseModel):
    items: list[RejillaDTO]
    catalogo_version: str
    provisional: bool


class ConductoDTO(BaseModel):
    id: str
    nombre: str
    diametro_pulgadas: float
    diametro_cm: float
    area_cm2: float
    factor_obturacion: float | None = None


class ListaConductosDTO(BaseModel):
    items: list[ConductoDTO]
    catalogo_version: str
    provisional: bool


class CasoDTO(BaseModel):
    id: int
    nombre: str
    recinto: RecintoDTO
    artefactos: list[ArtefactoDTO]
    numeral_esperado: str | None = None
    relacion_esperada: float | None = None
    resultado_esperado: str | None = None


class ListaCasosDTO(BaseModel):
    items: list[CasoDTO]


class ListaParametrosDTO(BaseModel):
    items: list[ConstanteDTO]


# --- Contenido y taller -----------------------------------------------------


class BloqueDTO(BaseModel):
    tipo: Literal["texto", "imagen", "nota", "definicion", "tabla"]
    contenido: str | None = None
    url: str | None = None
    alt: str | None = None


class PaginaDTO(BaseModel):
    slug: str
    titulo: str
    numerales: list[str] = Field(default_factory=list)
    bloques: list[BloqueDTO] = Field(default_factory=list)


class RespuestaAprendizDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relacion_m3_kw: float | None = None
    veredicto: VeredictoDTO | None = None
    area_libre_cm2: float | None = None


class SolicitudIntentoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    respuesta: RespuestaAprendizDTO


class IntentoDTO(BaseModel):
    id: str
    correcto: bool
    retroalimentacion: str
    esperado: SolicitudIntentoDTO | None = None


class EstadoDTO(BaseModel):
    estado: Literal["ok", "degradado"]
    version: str
    motor_version: str
    norma_version: str
