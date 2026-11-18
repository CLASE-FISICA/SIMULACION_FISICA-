"""Motor de cálculo de ventilación según la NTC 3631.

Paquete Python puro: no depende de FastAPI ni de la base de datos. La API
(`app/api`) construye una `EntradaEvaluacion` y llama a `evaluar`.
"""

from app.domain.catalogos import (
    CONDUCTOS_PROVISIONALES,
    REJILLAS_PROVISIONALES,
    VENTILADORES_PROVISIONALES,
    seleccionar_conducto,
    seleccionar_rejilla,
    seleccionar_ventilador,
)
from app.domain.metodos import Catalogos
from app.domain.modelos import (
    Advertencia,
    Artefacto,
    Conducto,
    ContextoRecinto,
    EntradaEvaluacion,
    EntradaInvalida,
    ErrorDominio,
    EstadoMetodo,
    Geometria,
    Metodo,
    Nivel,
    OpcionesMetodo,
    OpcionMetodo,
    Paso,
    Recinto,
    Recomendacion,
    Rejilla,
    ResultadoDimensionamiento,
    ResultadoEstandar,
    ResultadoEvaluacion,
    TipoArtefacto,
    TipoRecinto,
    Ventilador,
)
from app.domain.motor import evaluar
from app.domain.normativa import (
    AVISO_NO_CERTIFICA,
    CONSTANTES,
    VERSION_MOTOR,
    VERSION_NORMA,
    Constante,
    Parametros,
)
from app.domain.unidades import UnidadLongitud, UnidadPotencia, a_kw, a_metros

__all__ = [
    "AVISO_NO_CERTIFICA",
    "CONDUCTOS_PROVISIONALES",
    "CONSTANTES",
    "REJILLAS_PROVISIONALES",
    "VENTILADORES_PROVISIONALES",
    "VERSION_MOTOR",
    "VERSION_NORMA",
    "Advertencia",
    "Artefacto",
    "Catalogos",
    "Conducto",
    "Constante",
    "ContextoRecinto",
    "EntradaEvaluacion",
    "EntradaInvalida",
    "ErrorDominio",
    "EstadoMetodo",
    "Geometria",
    "Metodo",
    "Nivel",
    "OpcionMetodo",
    "OpcionesMetodo",
    "Parametros",
    "Paso",
    "Recinto",
    "Recomendacion",
    "Rejilla",
    "ResultadoDimensionamiento",
    "ResultadoEstandar",
    "ResultadoEvaluacion",
    "TipoArtefacto",
    "TipoRecinto",
    "UnidadLongitud",
    "UnidadPotencia",
    "Ventilador",
    "a_kw",
    "a_metros",
    "evaluar",
    "seleccionar_conducto",
    "seleccionar_rejilla",
    "seleccionar_ventilador",
]
