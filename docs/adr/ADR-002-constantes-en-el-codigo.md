# ADR-002 — Las constantes normativas viven en el código

- **Estado:** aceptado
- **Fecha:** 11 de noviembre de 2026
- **Afecta a:** BE1 (motor), BD2 (datos semilla), BE2 (contrato)

## Contexto

El plan general proponía que el motor leyera las constantes desde la base de datos
("el motor lee las constantes de la base, no del código"). La arquitectura del mismo plan
pide un motor sin dependencias que se pruebe sin base de datos. Las dos cosas no pueden
ser ciertas a la vez.

El riesgo concreto: si un administrador cambia 3,4 por 3,0 en una tabla, todos los
veredictos cambian y ninguna prueba lo detecta.

## Decisión

Las constantes viven en `app/domain/constants.py`, tipadas y con su numeral. Cada una es un
objeto `Constante` con valor, unidad, numeral y descripción.

La base de datos puede guardar una copia para consulta y para el módulo de aprendizaje
(tarea BD05), pero el motor nunca la lee. Una prueba verifica que la copia coincide con el
código y falla si divergen.

## Consecuencias

- Cambiar un factor es un cambio de código con revisión, prueba y versión de motor.
- No hay forma de alterar un veredicto sin pasar por el repositorio.
- El administrador no puede editar la norma desde la interfaz, que es precisamente lo
  que se busca.
- Si la norma cambia, se publica una versión nueva de la norma y del motor; las
  evaluaciones guardadas conservan la versión con la que se calcularon.
