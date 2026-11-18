# ADR-001 — El dominio es Python puro

- **Estado:** aceptado
- **Fecha:** 11 de noviembre de 2026
- **Afecta a:** BE1 (motor), BE2 (API), BE4 (pruebas)

## Contexto

El motor implementa una norma técnica y sus veredictos son la razón de ser del producto.
Necesita probarse contra los ocho casos del libro en cada cambio, sin base de datos, sin
servidor y sin red.

## Decisión

`app/domain` no importa FastAPI, ni SQLAlchemy, ni ningún cliente de red. Solo depende de
pydantic (validación y serialización) y de la biblioteca estándar.

`app/api` es un adaptador de entrada. `app/infra` es un adaptador de salida.

## Consecuencias

- El motor se prueba con `pytest` en milisegundos y sin fixtures de infraestructura.
- Una versión de escritorio o una API para un tercero no exige reescribir el cálculo.
- Hay una capa de mapeo entre dominio y contrato (ver ADR-003, D6) que para un proyecto
  pequeño parece burocracia.
- Si el dominio necesitara algo de la base de datos, hay que pasarlo por parámetro:
  las constantes normativas, por ejemplo, viven en el código y no se consultan.
