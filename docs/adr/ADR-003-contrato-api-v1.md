# ADR-003 — Contrato de la API v1

- **Estado:** propuesto
- **Fecha:** 11 de noviembre de 2026
- **Decide:** BE2 (dueño del contrato)
- **Afecta a:** Frontend (FE1, FE2, FE3), Backend (BE1, BE3, BE4), Documentación (DO2)
- **Cierra:** BE07 (contrato inicial), habilita BE10 (congelamiento en el sprint 3)

## Contexto

Quince personas van a consumir esta API. El frontend arranca el primer día y no puede
esperar al motor; el motor está siendo escrito en paralelo por otra persona; el contrato
tiene fecha de congelamiento en la semana 6. Si cada uno adivina la forma de los datos,
la integración se hace en la semana 8 con cuarenta errores, que es exactamente lo que el
plan quiere evitar.

El contrato es, por tanto, un artefacto de coordinación antes que un documento técnico.
Se escribe primero y el código se adapta a él.

## Decisiones

### D1 — El OpenAPI se escribe a mano, no se genera

`docs/contrato/openapi.yaml` es la fuente de verdad y se versiona en el repositorio. FastAPI
genera su propio esquema; una prueba compara los dos y falla si divergen.

**Por qué:** si el contrato se genera desde el código, cambia cada vez que alguien toca un
modelo, y el frontend se entera por sorpresa. Escrito a mano, cambiar el contrato es un acto
deliberado que pasa por revisión.

**Cómo se verifica:** `tests/test_contrato.py` compara rutas, códigos de respuesta y nombres
de campos del esquema generado contra el YAML versionado.

### D2 — `snake_case` en todo el JSON

Nombres de campos, parámetros de consulta y claves de respuesta en `snake_case`.
Sin excepciones, incluido lo que venga de la base de datos.

**Por qué:** el back es Python y la base es PostgreSQL; ambos son `snake_case`. Convertir en
el borde crea dos vocabularios y un mapeo más donde equivocarse. El frontend convierte a
`camelCase` donde le convenga, con los tipos generados.

### D3 — Errores en formato RFC 9457 con un `code` estable

Todo error, en cualquier endpoint, responde `application/problem+json`:

```json
{
  "type": "https://simulador-ntc3631.example/problemas/validacion",
  "title": "Entrada inválida",
  "status": 422,
  "detail": "El campo alto_m debe ser mayor que cero.",
  "instance": "/v1/evaluaciones/preview",
  "code": "validacion",
  "errors": [{"campo": "recinto.alto_m", "mensaje": "debe ser mayor que cero"}]
}
```

`code` es un vocabulario cerrado y no cambia nunca: `validacion`, `sin_artefactos`,
`no_encontrado`, `sin_permiso`, `conflicto_idempotencia`, `regla_no_implementada`.
`detail` es texto para humanos y puede cambiar.

**Por qué:** sin esto, cada endpoint inventa su forma de fallar y el frontend escribe un
`if` por endpoint. Y un cliente que decide por `detail` se rompe el día que se corrige una
falta de ortografía.

### D4 — Paginación por página, con sobre fijo

```json
{"items": [], "total": 0, "page": 1, "size": 20, "pages": 0}
```

`size` máximo 100, por defecto 20, `page` empieza en 1.

**Por qué:** el panel del instructor lista por ficha, y una ficha puede tener doscientos
aprendices con varias simulaciones cada uno. Devolver todo funciona en la demo y tumba la
API cuando llegue el primer grupo grande. Cursor sería mejor a escala, pero la pantalla
necesita el total para paginar; se empieza con página y se migra si hace falta.

### D5 — Identificadores UUID v4

Ninguna ruta expone un entero autoincremental.

**Por qué:** un `id: 37` revela cuántas evaluaciones hay en el sistema y permite enumerar
las ajenas probando números. Con UUID, el intento de leer lo que no es tuyo falla por
inexistencia, no por permisos, y eso además no filtra información.

### D6 — El DTO es una copia del dominio, no el modelo del dominio

`app/api` define sus propios esquemas y mapea desde `app.domain`. El modelo `Resultado` del
motor nunca se serializa directamente.

**Por qué:** si el contrato es el modelo del dominio, BE1 añade un campo y el contrato cambió
sin que nadie lo decidiera; peor aún, BE1 renombra un campo y rompe el frontend desde otro
repositorio lógico. Con copia explícita, el contrato lo controla BE2 y el dominio puede
evolucionar. El costo es una función de mapeo por entidad: treinta líneas, y es donde se
pone la prueba.

### D7 — Congelamiento aditivo en la semana 6

A partir del cierre del sprint 3:

- Se pueden **añadir** campos opcionales.
- No se puede **renombrar** ni **eliminar** un campo.
- No se puede **cambiar** el tipo de un campo ni volverlo obligatorio.
- No se puede **cambiar** el significado de un valor de enum.
- Un cambio incompatible es una `v2`, con `/v2` en la ruta y convivencia de ambas versiones.

**Por qué:** BE1 estará metiendo el árbol de decisión justo cuando toca congelar. Sin una
regla escrita, "congelar" significa "hasta que cambie algo", que es nunca.

`Resultado.requerimientos` existe desde la v0; llega vacío si solo se evalúa el método
estándar, y contiene propuestas de dimensionamiento cuando se pide un método alterno.
No acredita ejecución de obra ni certifica la instalación.

### D8 — La generación del PDF va por cola desde el diseño

El mecanismo se decide ahora; la implementación entra en el sprint 4.

`GET /v1/evaluaciones/{id}/reporte.pdf` devuelve el PDF si está listo y `409` con
`code: en_generacion` mientras se produce. La generación corre en un proceso aparte.

**Por qué:** generar PDF con WeasyPrint bloquea el proceso. Con una demo de tres personas no
se nota; con un grupo de treinta simulando a la vez, la API deja de responder y el problema
aparece en el peor momento, que es siempre el día de la sustentación.

### D9 — Cada resultado viaja con su versión de norma y de motor

`norma_version` y `motor_version` son obligatorios en `Resultado` y se guardan con la
evaluación.

**Por qué:** un reporte emitido en marzo no puede cambiar de veredicto porque en junio se
corrigió un factor. Es el requisito que sostiene la trazabilidad del producto, y BE3 lo
necesita para BE15.

### D10 — Catálogos públicos de solo lectura

`/v1/catalogos/*` y `/v1/contenido/*` no requieren sesión. Todo lo demás sí.

**Por qué:** el frontend del simulador necesita el catálogo de rejillas antes de que el
aprendiz inicie sesión (pantalla de bienvenida y ejemplos), y el módulo de aprendizaje debe
poder abrirse sin cuenta. No hay datos personales en esos recursos.

## Consecuencias

**A favor**

- El frontend arranca en el día 3 del sprint 0 con mock y tipos, sin esperar al motor.
- Los cambios de contrato son visibles y revisables, no accidentes.
- Los errores tienen una sola forma y un vocabulario estable.
- El expediente es auditable: cada resultado lleva su versión de norma.

**En contra**

- Hay que mantener dos descripciones de la misma cosa (YAML versionado y esquemas de
  FastAPI) y una prueba que las compara. Es trabajo real.
- Una capa de mapeo entre dominio y API que para un proyecto pequeño parece burocracia.
- Si el instructor cambia de criterio en el sprint 4, la regla de congelamiento aditivo
  obliga a añadir campos en vez de corregir los existentes, y quedan campos muertos.

## Lo que este ADR no decide

- La autenticación y las cookies: es de BE3 (SE01) y se consume aquí.
- El esquema de la base de datos: es de BD1.
- Qué rejilla gana: es del motor (BE1) y del catálogo (BD2).
- Si el factor 0,75 del conducto aplica: es del instructor.

## Cómo se comprueba que sigue vigente

1. `pytest tests/test_contrato.py` compara el esquema generado con el YAML: si divergen, falla.
2. Todo campo nuevo en el YAML lleva su `description` y, si es opcional, la razón.
3. El changelog del contrato vive en `docs/contrato/CHANGELOG.md` con fecha y autor por
   cambio incompatible.
4. Al cierre del sprint 3 se etiqueta el commit: `contrato-v1.0`. De ahí en adelante, ese
   archivo es la referencia.
