"""Aplicación FastAPI.

El navegador nunca calcula: envía los datos, esta capa llama al motor (app.domain) y
devuelve el resultado con su traza. Ver ADR-001 y ADR-003.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.errors import registrar_manejadores
from app.api.routers import catalogos, contenido, estado, evaluaciones, normativa, taller

DESCRIPCION = """\
Verifica si un recinto con artefactos a gas cumple los requisitos de ventilación de la
NTC 3631 y devuelve el paso a paso, con el numeral que respalda cada decisión.

La herramienta verifica y documenta. **No certifica instalaciones.**

El contrato de esta API se congela en la semana 6 (ADR-003). A partir de ahí solo crece
de forma aditiva: campos nuevos opcionales, nunca renombrados ni eliminados.
"""


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Verificador de ventilación NTC 3631 — API v1",
        version=__version__,
        description=DESCRIPCION,
        contact={"name": "Equipo Backend — BE2"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    registrar_manejadores(app)

    app.include_router(estado.router)
    app.include_router(normativa.router)
    app.include_router(catalogos.router)
    app.include_router(evaluaciones.router)
    app.include_router(contenido.router)
    app.include_router(taller.router)

    return app


app = crear_app()
