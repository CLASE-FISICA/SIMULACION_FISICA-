# Verificador de ventilación — NTC 3631 (backend)

API que verifica si un recinto con artefactos a gas cumple los requisitos de ventilación de
la NTC 3631 y devuelve el paso a paso con el numeral que respalda cada decisión.

La herramienta **verifica y documenta. No certifica instalaciones.**

## Arranque

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

Documentación interactiva: http://localhost:8000/docs

## Estado actual

| Área | Estado |
|---|---|
| Motor: método estándar (4.1.1) y restricciones de ubicación | Implementado |
| Motor: aberturas (4.1.2, 4.2.1, 4.2.2, 4.3, 4.4, Anexo D) | Integrado desde BE1; validación normativa de métodos alternos pendiente |
| API: 13 rutas del contrato v1 | Implementadas |
| Contrato congelado | Pendiente (sprint 3); se añadieron campos opcionales para métodos alternos |
| Persistencia | En memoria, temporal hasta las migraciones de BD1 |
| Autenticación | Adaptador de desarrollo; la real es de BE3 (BE13/SE01) |
| Reporte PDF | Pendiente (sprint 4, BE11) |

## Estructura

```
app/
  domain/       motor normativo, Python puro (ADR-001)
  catalog/      rejillas y conductos (vive en app/infra/catalogo.py por ahora)
  application/  casos de uso
  api/          routers, DTO, errores RFC 9457
  infra/        repositorios y contenido
docs/
  adr/          decisiones de arquitectura
  contrato/     openapi.yaml, fuente de verdad del contrato (ADR-003, D1)
tests/
  test_contrato.py   compara el YAML versionado con el esquema de FastAPI
  test_api.py        contrato, aislamiento por rol y errores
  test_golden_casos.py  los 8 casos del libro
  test_reglas.py     reglas y bloqueos
  test_normativa.py  las constantes y sus numerales
```

El motor alterno proviene del commit `e7f28ac` de la rama `backend` en
`CLASE-FISICA/SIMULACION_FISICA-`. Se incorporó en `app/domain` sin sobrescribir
el motor histórico; `app/application/motor_be1.py` adapta sus datos al contrato v1.
Un `requerimiento` describe una obra propuesta, no acredita que esté construida.
El catálogo comercial sigue siendo provisional.

## Calidad

```bash
ruff check .
mypy app
pytest -q
```

Nada entra a `main` con pruebas en rojo. Los ocho casos del libro son puerta de salida de
cada release.

## Sesión en desarrollo

Mientras BE3 implementa el JWT, la API acepta cabeceras para suplantar un usuario:

```
X-Dev-Usuario: aprendiz-1
X-Dev-Rol: aprendiz        # aprendiz | instructor | administrador
X-Dev-Ficha: ficha-1
```

Solo funciona con `DEV_MODE=true`, que es el valor por defecto en local.

## Variables de entorno

| Variable | Por defecto | Para qué |
|---|---|---|
| `DEV_MODE` | `true` | Permite suplantar usuario con cabeceras |
| `NORMA_VERSION` | `NTC 3631 (edición por confirmar con el instructor)` | Versión enviada en resultados, salud y normativa; confirmar antes de publicar |
| `CATALOGO_PROVISIONAL` | `true` | Marca el catálogo como no validado con proveedor |
| `PDF_HABILITADO` | `false` | Activa la generación del reporte (sprint 4) |
