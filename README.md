# Base de datos: Simulación matemática aplicada a ventilación NTC 3631

Archivo: `ventilacion_ntc3631.db` (SQLite 3)
Origen: `Simulación_matemática_aplicada_a_ventilacion_NTC_3631.xlsx`

Contiene 17 tablas y 1 vista. Los valores son los calculados en Excel (no se guardaron las fórmulas).

## Modelo de relaciones

```
tipo_recinto ─┐
metodo_ventilacion ─┤
tipo_ventilacion ─┼─► caso ─┬─► recinto (1:1)
construccion ─┘          ├─► artefacto (1:N)
                         ├─► evaluacion_metodo_estandar (1:1)
                         ├─► calculo_abertura (1:1, casos 1-7)
                         └─► suministro_mecanico (1:1, caso 8)

taller ─► taller_artefacto (1:N)
```

Tablas sin relaciones: `parametro_normativo`, `rejilla_comercial`, `volumen_critico_por_potencia`, `definicion`, `contenido_hoja`.

## Catálogos

| Tabla | Filas | Contenido |
|---|---|---|
| `tipo_recinto` | 3 | Ventilación; Recintos ubicado < 260msnm; Suministro mecánico de aire |
| `metodo_ventilacion` | 1 | Método estándar |
| `tipo_ventilacion` | 3 | Todo el aire del interior; Todo el aire del exterior; Suministro aire mecánico |
| `construccion` | 7 | Dos aberturas interiores; Abertura diferentes pisos; Dos aberturas; Conducto vertical; Conducto horizontal; Una abertura; Suministro mecánico de aire |

Columnas: `id`, `nombre`.

## Parámetros y tablas de referencia

### `parametro_normativo` (19 filas)
Constantes de la norma y de conversión.
Columnas: `id`, `clave`, `valor`, `unidad`, `numeral_ntc`, `descripcion`.

| Clave | Valor | Unidad | Numeral |
|---|---|---|---|
| volumen_critico_m3_por_kw | 3,4 | m3/kW | 4.1.1 |
| area_libre_interior_mismo_piso | 22 | cm2/kW | 4.1.2 a) |
| area_libre_interior_minima_mismo_piso | 645 | cm2 | 4.1.2 a) |
| area_libre_interior_diferentes_pisos | 44 | cm2/kW | 4.1.2 b) |
| area_libre_exterior_directa_o_vertical | 6 | cm2/kW | 4.2.1 a) |
| area_libre_exterior_horizontal | 11 | cm2/kW | 4.2.1 b) |
| area_libre_exterior_una_abertura | 11 | cm2/kW | 4.2.2 |
| area_libre_menor_260_msnm | 150 | cm2/kW | Anexo D |
| dimension_minima_abertura | 8 | cm | 4.2 |
| area_minima_abertura | 64 | cm2 | 4.2 |
| factor_area_efectiva_rejilla | 0,6 | - | 4.1.2 |
| factor_area_efectiva_conducto | 0,75 | - | Hoja Simulación |
| altura_abertura_superior_min | 180 | cm | 4.1.2 / 4.2.1 |
| altura_abertura_inferior_max | 30 | cm | 4.1.2 / 4.2.1 |
| factor_suministro_mecanico_aire | 0,034 | m3/min-kW | 4.4 |
| altura_promedio_construccion_colombia | 2,3 | m | Recomendación |
| descuento_volumen_muebles | 0,20 | - | Recomendación (no norma) |
| btu_hr_por_kw | 3412,142 | BTU/hr/kW | Conversión |
| mj_hr_por_kw | 3,6 | MJ/hr/kW | Conversión |

### `rejilla_comercial` (4 filas)
Rejillas de referencia. Columnas: `id`, `codigo`, `tipo`, `area_total_cm2`, `factor_area_efectiva`, `area_efectiva_cm2`.

| Código | Tipo | Área total (cm2) | Área efectiva (cm2) |
|---|---|---|---|
| Nº1 | 15X15 | 225 | 135 |
| Nº2 | 20X20 | 400 | 240 |
| Nº3 | 25x25 | 625 | 375 |
| Nº5 | 30X30 | 900 | 540 |

### `volumen_critico_por_potencia` (50 filas)
Volumen mínimo del recinto según la potencia (3,4 m3 por kW). Columnas: `potencia_kw` (1 a 50), `volumen_critico_m3` (3,4 a 170).

## Casos pedagógicos

### `caso` (8 filas)
Columnas: `id`, `nombre`, `titulo`, `enunciado` (solo casos 4, 5 y 8), `metodo_inicial_id`, `metodo_requerido`, `tipo_ventilacion_id`, `construccion_id`.

| Caso | Método requerido | Tipo de ventilación | Construcción |
|---|---|---|---|
| 1 | Combinación de espacios en el mismo piso | Todo el aire del interior | Dos aberturas interiores |
| 2 | Combinación de espacios en diferentes pisos | Todo el aire del interior | Abertura diferentes pisos |
| 3 | Método 1 | Todo el aire del exterior | Dos aberturas |
| 4 | Método 1 | Todo el aire del exterior | Conducto vertical |
| 5 | Método 1 | Todo el aire del exterior | Conducto horizontal |
| 6 | Método 2 | Todo el aire del exterior | Una abertura |
| 7 | Recintos ubicado < 260msnm | Todo el aire del exterior | Una abertura |
| 8 | Combinación de espacios en el mismo piso (*) | Suministro aire mecánico | Suministro mecánico de aire |

(*) Así figura en el Excel; parece una inconsistencia del libro original.

### `recinto` (8 filas)
Columnas: `id`, `caso_id`, `tipo_recinto_id`, `ancho_m`, `fondo_m`, `altura_m`, `volumen_m3`.

| Caso | Ancho (m) | Fondo (m) | Altura (m) | Volumen (m3) |
|---|---|---|---|---|
| 1 | 1,9 | 1,8 | 2,4 | 8,208 |
| 2 | 3,5 | 4,0 | 2,3 | 32,2 |
| 3 | 3,0 | 6,0 | 2,4 | 43,2 |
| 4 | 5,0 | 6,0 | 2,4 | 72,0 |
| 5 | 5,0 | 6,0 | 2,4 | 72,0 |
| 6 | 3,0 | 6,0 | 2,4 | 43,2 |
| 7 | 3,0 | 6,0 | 2,4 | 43,2 |
| 8 | 6,0 | 6,0 | 3,0 | 108,0 |

### `artefacto` (13 filas)
Columnas: `id`, `caso_id`, `nombre`, `potencia_kw`, `marca`, `tipo`.
`marca` y `tipo` están vacías (el Excel no trae datos). En los casos 4 y 5 solo se conoce la potencia total (24 kW).

| Caso | Artefactos |
|---|---|
| 1 | Calentador 11,4 kW |
| 2 | Cocina 9,6 kW |
| 3, 6, 7 | Cocina 9,6 kW + Calentador 11,4 kW (21 kW) |
| 4, 5 | Total potencia instalada 24 kW |
| 8 | Estufa 15 kW + Horno 12 kW + Freidora 10 kW (37 kW) |

### `evaluacion_metodo_estandar` (8 filas)
Compara el volumen disponible con el volumen crítico de 3,4 m3/kW.
Columnas: `id`, `caso_id`, `potencia_total_kw`, `volumen_m3`, `relacion_m3_por_kw`, `volumen_critico_m3_por_kw`, `resultado`.

| Caso | Potencia (kW) | Volumen (m3) | m3/kW | Resultado |
|---|---|---|---|---|
| 1 | 11,4 | 8,208 | 0,72 | No cumple ventilación |
| 2 | 9,6 | 32,2 | 3,35 | No cumple ventilación |
| 3, 6, 7 | 21 | 43,2 | 2,06 | No cumple ventilación |
| 4, 5 | 24 | 72 | 3,00 | No cumple ventilación |
| 8 | 37 | 108 | 2,92 | No cumple ventilación |

### `calculo_abertura` (7 filas, casos 1 a 7)
Dimensionamiento de rejillas y conductos cuando no se cumple el método estándar.
Columnas: `id`, `caso_id`, `modelo_calculo`, `area_libre_min_cm2_por_kw`, `potencia_kw`, `area_abertura_cm2`, `area_libre_cm2`, `factor_utilizado`, `area_total_disponible_cm2`, `geometria`, `dimension_minima_cm`, `area_minima_abertura_cm2`, `lado_o_diametro_cm`, `diametro_comercial_pulg`, `rejilla_comercial`, `aberturas`, `ubicacion`.

| Caso | Modelo | cm2/kW | Área total disponible (cm2) | Resultado |
|---|---|---|---|---|
| 1 | Mismo piso | 22 | 1.075 | Rejilla 35x35, superior/inferior |
| 2 | Diferentes pisos | 44 | 704 | Rejilla 30x30, entre pisos |
| 3 | Método 1, dos rejillas | 6 | 210 | Rejilla 15x15, superior/inferior |
| 4 | Método 1, conducto vertical | 6 | 192 | Diámetro 15,6 cm (6,16 pulg) |
| 5 | Método 1, conducto horizontal | 11 | 440 | Lado construible 25 cm |
| 6 | Método 2, una rejilla | 11 | 385 | Rejilla 20x20 |
| 7 | Anexo D, < 260 msnm | 150 | 5.250 | Rejilla 90x60, a más de 1 m del piso |

Notas: en el caso 2 `area_libre_cm2` repite `area_abertura_cm2`; en el caso 5 el lado construible está en `rejilla_comercial` como texto.

### `suministro_mecanico` (1 fila, caso 8)
Columnas: `id`, `caso_id`, `factor_m3_min_kw`, `potencia_kw`, `caudal_m3_min`, `caudal_m3_h`, `tipo_ventilador`, `capacidad_ventilador_m3_h`, `alimentacion`, `extraccion_cocina_m3_h`, `caudal_total_m3_h`, `tipo_gas`.
Valores: factor 0,034 m3/min-kW, 37 kW, 1,258 m3/min (75,48 m3/h), ventilador centrífugo eléctrico, extracción de cocina 1.800 m3/h, total 1.875,48 m3/h, gas natural.

## Taller práctico

### `taller` (3 filas)
Columnas: `id`, `numero`, `enunciado`. Enunciados de los 3 ejercicios.

### `taller_artefacto` (4 filas)
Columnas: `id`, `taller_id`, `nombre`, `valor`, `unidad`, `potencia_kw`.

| Taller | Artefacto | Valor | Potencia (kW) |
|---|---|---|---|
| 1 | Estufa | 25.000 BTU/hr | 7,33 |
| 1 | Horno | 10 MJ/hr | 2,78 |
| 2 | Cubierta | 8 kW | 8 |
| 2 | Horno | 4 kW | 4 |

El taller 3 no tiene artefactos cargados. No se guardaron los resultados calculados del taller 1 (volumen 25,85 m3; 2,56 m3/kW).

## Contenido textual

### `definicion` (8 filas)
Columnas: `id`, `termino`, `descripcion`, `fuente_hoja`.
Términos: Aire circulante, Aire de combustión, Aire de dilución, Aire de renovación, Infiltración de aire, Potencia nominal, Recinto interior, Combustión.

### `contenido_hoja` (206 filas)
Fragmentos de texto de las hojas explicativas (Inicio, Objetivo, Generalidades, Reacción combustión, Conceptos clave, 4.1.1, 4.2.1, 4.2.2, 4.3, 4.4, 5 y Anexo D).
Columnas: `id`, `hoja`, `celda`, `texto`.

## Vista

### `v_resumen_casos`
Une `caso`, `recinto`, `evaluacion_metodo_estandar`, `calculo_abertura`, `tipo_ventilacion` y `construccion`.
Columnas: `caso`, `metodo_requerido`, `tipo_ventilacion`, `construccion`, `ancho_m`, `fondo_m`, `altura_m`, `volumen_m3`, `potencia_total_kw`, `relacion_m3_por_kw`, `resultado`, `area_total_disponible_cm2`, `rejilla_comercial`, `aberturas`.

## Consultas de ejemplo

```sql
-- Resumen de todos los casos
SELECT * FROM v_resumen_casos;

-- Casos que no cumplen el método estándar, de mayor a menor déficit
SELECT caso_id, relacion_m3_por_kw,
       ROUND(volumen_critico_m3_por_kw - relacion_m3_por_kw, 2) AS deficit_m3_por_kw
FROM evaluacion_metodo_estandar
WHERE resultado = 'No cumple ventilación'
ORDER BY deficit_m3_por_kw DESC;

-- Potencia total por caso a partir de los artefactos
SELECT caso_id, SUM(potencia_kw) AS potencia_total_kw
FROM artefacto GROUP BY caso_id;

-- Buscar texto normativo
SELECT hoja, celda, texto FROM contenido_hoja WHERE texto LIKE '%8 cm%';
```
