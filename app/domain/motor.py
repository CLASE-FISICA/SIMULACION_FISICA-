"""Punto de entrada del motor: evalúa un recinto de principio a fin."""

from app.domain.bitacora import Bitacora
from app.domain.estandar import metodo_estandar
from app.domain.metodos import Catalogos, DatosCalculo, dimensionar
from app.domain.modelos import (
    NOMBRE_METODO,
    EntradaEvaluacion,
    EstadoMetodo,
    Metodo,
    Nivel,
    ResultadoDimensionamiento,
    ResultadoEvaluacion,
)
from app.domain.normativa import AVISO_NO_CERTIFICA
from app.domain.recomendador import recomendar, restricciones_ubicacion


def evaluar(entrada: EntradaEvaluacion, catalogos: Catalogos | None = None) -> ResultadoEvaluacion:
    """Método estándar, restricciones, método propuesto y, si se pide, dimensionamiento.

    Lanza `EntradaInvalida` o `ErrorDominio` cuando no se puede calcular.
    """
    b = Bitacora()
    estandar = metodo_estandar(entrada.recinto, entrada.artefactos, entrada.parametros, b)
    bloqueado = restricciones_ubicacion(entrada.recinto, entrada.artefactos, entrada.contexto, b)
    recomendacion = recomendar(estandar, entrada.artefactos, entrada.contexto, bloqueado)

    dimensionamiento: ResultadoDimensionamiento | None = None
    metodo = entrada.metodo
    if metodo is not None and metodo is not Metodo.ESTANDAR and estandar.potencia_total_kw > 0:
        if estandar.cumple:
            b.advertir(Nivel.INFO,
                       "El recinto ya cumple el método estándar; el dimensionamiento del "
                       "método alterno es solo ilustrativo.", "4.1.1")
        descartado = next((o for o in recomendacion.descartados if o.metodo is metodo), None)
        if descartado is not None and descartado.estado is EstadoMetodo.NO_APLICABLE:
            b.advertir(Nivel.ADVERTENCIA,
                       f"{NOMBRE_METODO[metodo]} no aplica a este recinto: {descartado.motivo}",
                       descartado.numeral)
        datos = DatosCalculo(
            potencia_kw=estandar.potencia_total_kw,
            volumen_util_m3=estandar.volumen_util_m3,
            artefactos=entrada.artefactos,
            opciones=entrada.opciones,
            parametros=entrada.parametros,
            catalogos=catalogos or Catalogos(),
        )
        dimensionamiento = dimensionar(metodo, datos, b)

    return ResultadoEvaluacion(
        estandar=estandar,
        dimensionamiento=dimensionamiento,
        recomendacion=recomendacion,
        pasos=b.pasos,
        advertencias=b.advertencias,
        parametros=entrada.parametros,
        aviso=AVISO_NO_CERTIFICA,
    )