"""Repositorio de evaluaciones, en memoria.

TEMPORAL: la persistencia real es PostgreSQL y la define BD1 (historias BD01, BD03). Este
repositorio existe para que la API y el frontend trabajen desde el sprint 0 sin esperar
las migraciones, y para fijar la interfaz que después implementará la base de datos.

Todo lo que hay aquí tiene el mismo contrato que tendrá la versión SQL: crear, obtener,
listar con aislamiento por rol, eliminar.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.api.dto import ResultadoDTO, SolicitudEvaluacionDTO


class NoEncontrado(Exception):
    """La evaluación no existe o no pertenece a quien la pide."""


@dataclass
class EvaluacionAlmacenada:
    id: str
    creada_en: datetime
    aprendiz_id: str
    ficha_id: str | None
    entradas: SolicitudEvaluacionDTO
    resultado: ResultadoDTO


@dataclass
class Filtros:
    page: int = 1
    size: int = 20
    ficha_id: str | None = None
    aprendiz_id: str | None = None
    veredicto: str | None = None
    orden: str = "fecha_desc"


class RepositorioEvaluaciones:
    def __init__(self) -> None:
        self._items: dict[str, EvaluacionAlmacenada] = {}
        self._idempotencia: dict[str, str] = {}
        self._lock = threading.Lock()

    def crear(
        self,
        *,
        aprendiz_id: str,
        entradas: SolicitudEvaluacionDTO,
        resultado: ResultadoDTO,
        idempotency_key: str | None = None,
    ) -> EvaluacionAlmacenada:
        with self._lock:
            if idempotency_key and idempotency_key in self._idempotencia:
                return self._items[self._idempotencia[idempotency_key]]
            almacenada = EvaluacionAlmacenada(
                id=str(uuid.uuid4()),
                creada_en=datetime.now(UTC),
                aprendiz_id=aprendiz_id,
                ficha_id=entradas.ficha_id,
                entradas=entradas,
                resultado=resultado,
            )
            self._items[almacenada.id] = almacenada
            if idempotency_key:
                self._idempotencia[idempotency_key] = almacenada.id
            return almacenada

    def obtener(self, evaluacion_id: str, *, aprendiz_id: str | None = None) -> EvaluacionAlmacenada:
        almacenada = self._items.get(evaluacion_id)
        if almacenada is None:
            raise NoEncontrado(evaluacion_id)
        if aprendiz_id is not None and almacenada.aprendiz_id != aprendiz_id:
            # Se responde "no existe" a propósito: no se filtra que el recurso exista.
            raise NoEncontrado(evaluacion_id)
        return almacenada

    def listar(self, filtros: Filtros, *, alcance: str | None = None) -> tuple[list[EvaluacionAlmacenada], int]:
        items = list(self._items.values())
        if alcance is not None:
            # alcance es el id del aprendiz cuando el rol solo puede ver lo propio.
            items = [i for i in items if i.aprendiz_id == alcance]
        if filtros.ficha_id:
            items = [i for i in items if i.ficha_id == filtros.ficha_id]
        if filtros.aprendiz_id:
            items = [i for i in items if i.aprendiz_id == filtros.aprendiz_id]
        if filtros.veredicto:
            items = [i for i in items if i.resultado.veredicto == filtros.veredicto]
        items.sort(key=lambda i: i.creada_en, reverse=filtros.orden == "fecha_desc")
        total = len(items)
        inicio = (filtros.page - 1) * filtros.size
        return items[inicio : inicio + filtros.size], total

    def eliminar(self, evaluacion_id: str, *, aprendiz_id: str | None = None) -> None:
        with self._lock:
            self.obtener(evaluacion_id, aprendiz_id=aprendiz_id)
            del self._items[evaluacion_id]

    def vaciar(self) -> None:
        """Solo para pruebas."""
        with self._lock:
            self._items.clear()
            self._idempotencia.clear()


repositorio = RepositorioEvaluaciones()
