"""Modelos de entrada y salida del motor de cálculo.

Son dataclasses inmutables sin dependencias externas: la API (BE-08) las
convierte a esquemas Pydantic y la persistencia las guarda tal cual.
"""

import math
from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.normativa import VERSION_MOTOR, VERSION_NORMA, Parametros
from app.domain.unidades import UnidadLongitud, UnidadPotencia, a_kw, a_metros


class ErrorDominio(Exception):
    """Error de las reglas del motor."""


class EntradaInvalida(ErrorDominio):
    """Un dato de entrada no cumple las condiciones mínimas para calcular."""

    def __init__(self, campo: str, mensaje: str) -> None:
        super().__init__(f"{campo}: {mensaje}")
        self.campo = campo
        self.mensaje = mensaje


# --- Catálogos de opciones -------------------------------------------------


class TipoArtefacto(StrEnum):
    """Clasificación por la forma de tomar el aire y evacuar los productos."""

    A = "A"
    """Circuito abierto sin conducto de evacuación (cocinas, hornos)."""
    B = "B"
    """Circuito abierto con conducto de evacuación (calentadores de tiro natural)."""
    C = "C"
    """Circuito estanco o cámara estanca: no cuenta en la potencia agregada."""


class Metodo(StrEnum):
    """Métodos de ventilación que el motor sabe dimensionar."""

    ESTANDAR = "4.1.1"
    MISMO_PISO = "4.1.2a"
    DIFERENTES_PISOS = "4.1.2b"
    M1_DIRECTA = "4.2.1-directa"
    M1_CONDUCTO_VERTICAL = "4.2.1-vertical"
    M1_CONDUCTO_HORIZONTAL = "4.2.1-horizontal"
    M2_UNA_ABERTURA = "4.2.2"
    COMBINACION = "4.3"
    ANEXO_D = "anexo-d"
    SUMINISTRO_MECANICO = "4.4"


NOMBRE_METODO: dict[Metodo, str] = {
    Metodo.ESTANDAR: "Método estándar",
    Metodo.MISMO_PISO: "Combinación de espacios en el mismo piso",
    Metodo.DIFERENTES_PISOS: "Combinación de espacios en diferentes pisos",
    Metodo.M1_DIRECTA: "Método 1, dos aberturas directas al exterior",
    Metodo.M1_CONDUCTO_VERTICAL: "Método 1, conductos verticales",
    Metodo.M1_CONDUCTO_HORIZONTAL: "Método 1, conductos horizontales",
    Metodo.M2_UNA_ABERTURA: "Método 2, una abertura permanente",
    Metodo.COMBINACION: "Combinación de aire del interior y del exterior",
    Metodo.ANEXO_D: "Recintos ubicados a menos de 260 msnm",
    Metodo.SUMINISTRO_MECANICO: "Suministro mecánico de aire",
}

NUMERAL_METODO: dict[Metodo, str] = {
    Metodo.ESTANDAR: "4.1.1",
    Metodo.MISMO_PISO: "4.1.2 a)",
    Metodo.DIFERENTES_PISOS: "4.1.2 b)",
    Metodo.M1_DIRECTA: "4.2.1 a)",
    Metodo.M1_CONDUCTO_VERTICAL: "4.2.1 a)",
    Metodo.M1_CONDUCTO_HORIZONTAL: "4.2.1 b)",
    Metodo.M2_UNA_ABERTURA: "4.2.2",
    Metodo.COMBINACION: "4.3",
    Metodo.ANEXO_D: "Anexo D",
    Metodo.SUMINISTRO_MECANICO: "4.4",
}


METODOS_EXTERIORES: frozenset[Metodo] = frozenset({
    Metodo.M1_DIRECTA,
    Metodo.M1_CONDUCTO_VERTICAL,
    Metodo.M1_CONDUCTO_HORIZONTAL,
    Metodo.M2_UNA_ABERTURA,
})


class TipoRecinto(StrEnum):
    COCINA = "cocina"
    ZONA_DE_ROPAS = "zona_de_ropas"
    DORMITORIO = "dormitorio"
    BANO = "bano"
    PRIMER_SOTANO = "primer_sotano"
    BAJO_PRIMER_SOTANO = "bajo_primer_sotano"
    COMERCIAL = "comercial"
    INDUSTRIAL = "industrial"
    OTRO = "otro"


class Nivel(StrEnum):
    INFO = "info"
    ADVERTENCIA = "advertencia"
    BLOQUEANTE = "bloqueante"
    """La instalación no es admisible tal como está planteada."""


class Geometria(StrEnum):
    CUADRADA = "cuadrada"
    CIRCULAR = "circular"


# --- Entradas --------------------------------------------------------------


def _positivo(campo: str, valor: float) -> None:
    if not math.isfinite(valor) or valor <= 0:
        raise EntradaInvalida(campo, f"debe ser un número mayor que cero; se recibió {valor}")


def _no_negativo(campo: str, valor: float | None) -> None:
    if valor is not None and (not math.isfinite(valor) or valor < 0):
        raise EntradaInvalida(campo, f"no puede ser negativo; se recibió {valor}")


@dataclass(frozen=True, slots=True, kw_only=True)
class Artefacto:
    nombre: str
    potencia: float
    unidad: UnidadPotencia = UnidadPotencia.KW
    tipo: TipoArtefacto = TipoArtefacto.A
    marca: str | None = None
    diametro_conector_cm: float | None = None
    """Diámetro del conector de evacuación; lo usa el Método 2 (4.2.2)."""
    separacion_lateral_cm: float | None = None
    separacion_posterior_cm: float | None = None
    separacion_frontal_cm: float | None = None

    def __post_init__(self) -> None:
        _positivo(f"artefacto «{self.nombre}».potencia", self.potencia)
        for nombre in (
            "diametro_conector_cm",
            "separacion_lateral_cm",
            "separacion_posterior_cm",
            "separacion_frontal_cm",
        ):
            _no_negativo(f"artefacto «{self.nombre}».{nombre}", getattr(self, nombre))

    @property
    def potencia_kw(self) -> float:
        return a_kw(self.potencia, self.unidad)

    @property
    def cuenta_en_potencia(self) -> bool:
        """La norma excluye los artefactos de cámara estanca (Tipo C)."""
        return self.tipo is not TipoArtefacto.C


@dataclass(frozen=True, slots=True, kw_only=True)
class Recinto:
    ancho: float
    fondo: float
    altura: float
    unidad: UnidadLongitud = UnidadLongitud.M
    tipo: TipoRecinto = TipoRecinto.COCINA
    nombre: str | None = None

    def __post_init__(self) -> None:
        _positivo("recinto.ancho", self.ancho)
        _positivo("recinto.fondo", self.fondo)
        _positivo("recinto.altura", self.altura)

    @property
    def ancho_m(self) -> float:
        return a_metros(self.ancho, self.unidad)

    @property
    def fondo_m(self) -> float:
        return a_metros(self.fondo, self.unidad)

    @property
    def altura_m(self) -> float:
        return a_metros(self.altura, self.unidad)


@dataclass(frozen=True, slots=True, kw_only=True)
class OpcionesMetodo:
    """Datos adicionales que solo piden algunos métodos."""

    volumen_espacios_comunicados_m3: float | None = None
    """Volumen de los espacios interiores comunicados con el recinto (4.1.2 y 4.3)."""
    metodo_exterior_combinacion: Metodo = Metodo.M2_UNA_ABERTURA
    """Método del numeral 4.2 con el que se calcula la abertura exterior en 4.3."""
    interiores_en_diferentes_pisos: bool = False
    """En 4.3, si las aberturas interiores comunican con espacios de otro piso."""
    altitud_msnm: float | None = None
    """Altitud del recinto; el Anexo D solo aplica por debajo de 260 msnm."""
    extraccion_cocina_m3h: float = 0.0
    """Capacidad del sistema de extracción que el suministro mecánico debe reponer (4.4)."""

    def __post_init__(self) -> None:
        _no_negativo("opciones.volumen_espacios_comunicados_m3",
                     self.volumen_espacios_comunicados_m3)
        _no_negativo("opciones.extraccion_cocina_m3h", self.extraccion_cocina_m3h)
        if self.metodo_exterior_combinacion not in METODOS_EXTERIORES:
            raise EntradaInvalida(
                "opciones.metodo_exterior_combinacion",
                "debe ser un método del numeral 4.2",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextoRecinto:
    """Lo que se sabe del recinto para que el árbol de decisión proponga un método.

    None significa «no se sabe»: el método queda como condicional en vez de
    descartarse.
    """

    espacios_comunicados_mismo_piso: bool | None = None
    espacios_comunicados_diferentes_pisos: bool | None = None
    volumen_espacios_comunicados_m3: float | None = None
    tiene_muro_exterior: bool | None = None
    permite_conducto_vertical: bool | None = None
    permite_conducto_horizontal: bool | None = None
    permite_suministro_mecanico: bool | None = None
    altitud_msnm: float | None = None
    gas_mas_denso_que_aire: bool | None = None
    """True para GLP; False para gas natural."""

    def __post_init__(self) -> None:
        _no_negativo("contexto.volumen_espacios_comunicados_m3",
                     self.volumen_espacios_comunicados_m3)


# --- Salidas ---------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class Paso:
    """Un paso del cálculo, con la fórmula, la sustitución y su respaldo."""

    numero: int
    descripcion: str
    formula: str
    sustitucion: str
    resultado: float | str
    unidad: str
    numeral: str | None = None
    origen: str | None = None
    """Celda del Excel que hace el mismo cálculo."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Advertencia:
    nivel: Nivel
    mensaje: str
    numeral: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Rejilla:
    codigo: str
    ancho_cm: float
    alto_cm: float
    origen: str

    @property
    def area_total_cm2(self) -> float:
        return self.ancho_cm * self.alto_cm

    @property
    def nombre(self) -> str:
        return f"{self.ancho_cm:g}x{self.alto_cm:g}"

    def area_efectiva_cm2(self, factor_rejilla: float) -> float:
        return self.area_total_cm2 * factor_rejilla


@dataclass(frozen=True, slots=True, kw_only=True)
class Conducto:
    diametro_pulg: float

    @property
    def diametro_cm(self) -> float:
        return self.diametro_pulg * 2.54

    @property
    def area_cm2(self) -> float:
        return math.pi * self.diametro_cm**2 / 4


@dataclass(frozen=True, slots=True, kw_only=True)
class Ventilador:
    capacidad_m3h: float
    origen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultadoEstandar:
    potencia_total_kw: float
    potencia_excluida_kw: float
    """Potencia de los artefactos Tipo C, que no cuenta."""
    volumen_m3: float
    volumen_util_m3: float
    """Volumen después de restar el margen por muebles, si está activo."""
    volumen_requerido_m3: float
    potencia_maxima_kw: float
    """Potencia agregada máxima que admite el recinto por el método estándar."""
    relacion_m3_kw: float | None
    """None cuando no hay potencia que contar (solo artefactos Tipo C)."""
    cumple: bool
    veredicto: str
    numeral: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultadoDimensionamiento:
    metodo: Metodo
    nombre_metodo: str
    numeral: str
    numero_aberturas: int
    ubicacion: tuple[str, ...]
    area_libre_cm2: float | None = None
    """Área libre de cada abertura que exige la norma."""
    area_total_cm2: float | None = None
    """Área bruta de la rejilla o sección del conducto, tras el factor de diseño."""
    geometria: Geometria | None = None
    lado_cm: float | None = None
    diametro_cm: float | None = None
    rejilla_comercial: Rejilla | None = None
    conducto_comercial: Conducto | None = None
    lado_construible_cm: float | None = None
    factor_reduccion: float | None = None
    caudal_combustion_m3h: float | None = None
    caudal_total_m3h: float | None = None
    ventilador: Ventilador | None = None
    aberturas_interiores: "ResultadoDimensionamiento | None" = None
    """En 4.3, las aberturas hacia los espacios interiores (numeral 4.1.2)."""


class EstadoMetodo(StrEnum):
    APLICABLE = "aplicable"
    CONDICIONAL = "condicional"
    """Aplicaría si se confirma un dato que falta."""
    NO_APLICABLE = "no_aplicable"


@dataclass(frozen=True, slots=True, kw_only=True)
class OpcionMetodo:
    metodo: Metodo
    nombre: str
    numeral: str
    estado: EstadoMetodo
    motivo: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Recomendacion:
    metodo_propuesto: Metodo | None
    alternativas: tuple[OpcionMetodo, ...]
    descartados: tuple[OpcionMetodo, ...]
    advertencias: tuple[Advertencia, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class EntradaEvaluacion:
    recinto: Recinto
    artefactos: tuple[Artefacto, ...]
    metodo: Metodo | None = None
    """Método alterno a dimensionar; None para que solo se proponga."""
    opciones: OpcionesMetodo = field(default_factory=OpcionesMetodo)
    contexto: ContextoRecinto = field(default_factory=ContextoRecinto)
    parametros: Parametros = field(default_factory=Parametros)

    def __post_init__(self) -> None:
        if not self.artefactos:
            raise EntradaInvalida("artefactos", "debe haber al menos un artefacto")


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultadoEvaluacion:
    estandar: ResultadoEstandar
    dimensionamiento: ResultadoDimensionamiento | None
    recomendacion: Recomendacion | None
    pasos: tuple[Paso, ...]
    advertencias: tuple[Advertencia, ...]
    parametros: Parametros
    version_norma: str = VERSION_NORMA
    version_motor: str = VERSION_MOTOR
    aviso: str = ""
