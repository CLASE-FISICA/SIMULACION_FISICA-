"""Registro del paso a paso auditable de cada cálculo (BE-02)."""

from app.domain.modelos import Advertencia, Nivel, Paso
from app.domain.normativa import Constante


def fmt(valor: float, decimales: int = 2) -> str:
    """Número con coma decimal, como se escribe en la norma y en el Excel."""
    texto = f"{valor:,.{decimales}f}".replace(",", " ").replace(".", ",")
    if "," in texto:
        texto = texto.rstrip("0").rstrip(",")
    return texto


class Bitacora:
    """Acumula pasos y advertencias en el orden en que se calculan."""

    def __init__(self) -> None:
        self._pasos: list[Paso] = []
        self._advertencias: list[Advertencia] = []

    def paso(
        self,
        descripcion: str,
        formula: str,
        sustitucion: str,
        resultado: float | str,
        unidad: str,
        *,
        numeral: str | None = None,
        origen: str | None = None,
    ) -> float | str:
        self._pasos.append(Paso(
            numero=len(self._pasos) + 1,
            descripcion=descripcion,
            formula=formula,
            sustitucion=sustitucion,
            resultado=resultado,
            unidad=unidad,
            numeral=numeral,
            origen=origen,
        ))
        return resultado

    def constante(self, constante: Constante, valor: float | None = None) -> float:
        """Deja constancia de la constante que se usa y devuelve su valor."""
        usado = constante.valor if valor is None else valor
        etiqueta = "" if constante.es_norma else f" ({constante.numeral.lower()})"
        self.paso(
            f"{constante.descripcion}{etiqueta}",
            constante.clave,
            fmt(usado, 3),
            usado,
            constante.unidad,
            numeral=constante.numeral if constante.es_norma else None,
            origen=constante.origen,
        )
        return usado

    def advertir(self, nivel: Nivel, mensaje: str, numeral: str | None = None) -> None:
        self._advertencias.append(Advertencia(nivel=nivel, mensaje=mensaje, numeral=numeral))

    @property
    def pasos(self) -> tuple[Paso, ...]:
        return tuple(self._pasos)

    @property
    def advertencias(self) -> tuple[Advertencia, ...]:
        return tuple(self._advertencias)