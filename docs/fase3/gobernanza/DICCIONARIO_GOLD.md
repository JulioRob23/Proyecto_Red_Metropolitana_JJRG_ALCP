# Diccionario de Datos - Capa Gold

## Objetivo

Este documento define el significado oficial de los campos disponibles en
la capa Gold de la Red Metropolitana.

Para cada campo se documenta su significado, origen y transformación
principal. El objetivo es que los consumidores de datos puedan interpretar
Gold sin depender de conocer el código interno del pipeline.

La capa Gold se encuentra dividida en:

1. Modelo dimensional principal.
2. Vistas analíticas utilizadas por Tableau.

---

# 1. Modelo dimensional principal

## 1.1 dim_modo

**Grano:** una fila por modo de transporte.

**Origen:** información conformada de los cuatro sistemas de transporte.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `modo_key` | Llave sustituta del modo de transporte. | Generada en Gold para relacionar dimensiones y hechos. |
| `modo_codigo` | Código estandarizado del sistema. | Normalización de los nombres de los cuatro operadores. |
| `modo_nombre` | Nombre legible del modo de transporte. | Valor conformado para Transmetro, Transurbano, MetroRiel y Aerómetro. |

---

## 1.2 dim_zona

**Grano:** una fila por zona conformada.

**Origen:** zonas presentes en los catálogos y eventos integrados en Silver.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `zona_key` | Llave sustituta de la zona. | Generada en Gold. |
| `zona_nombre` | Nombre conformado de la zona o municipio. | Normalización realizada durante Silver para evitar distintas representaciones de una misma zona. |

---

## 1.3 dim_usuario

**Grano:** una fila por identidad conformada de usuario.

**Origen:** puente de identidad construido durante Silver.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `usuario_key` | Llave sustituta utilizada por Gold para identificar al usuario. | Generada en Gold a partir de la identidad conformada. |
| `usuario_id` | Identificador seudonimizado y conformado del usuario. | Derivado de la estrategia de identidad definida en Silver. No expone directamente el número original de tarjeta. |
| `cantidad_sistemas` | Cantidad de sistemas diferentes en los que fue observada la identidad. | Conteo de sistemas asociados al mismo `usuario_id`. |
| `sistemas_observados` | Lista de sistemas donde fue observada la identidad. | Agregación de los operadores relacionados al usuario. |
| `es_multimodal_aprox` | Indica si la identidad aparece en más de un sistema enlazable. | Verdadero cuando `cantidad_sistemas > 1`. Representa multimodalidad aproximada, no un transbordo confirmado. |
| `identidad_aislada` | Indica que la identidad no puede relacionarse confiablemente con los demás operadores. | Se utiliza principalmente para Aerómetro por no existir un crosswalk confiable con los otros identificadores. |

---

## 1.4 dim_tiempo

**Grano:** una fila por minuto del período analizado.

**Origen:** dimensión generada a partir del intervalo temporal del proyecto.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `tiempo_key` | Llave sustituta de tiempo utilizada por las tablas de hechos. | Generada en Gold para cada minuto. |
| `minuto_inicio` | Timestamp correspondiente al inicio del minuto. | Generado a partir del calendario de la dimensión. |
| `fecha` | Fecha calendario. | Derivada de `minuto_inicio`. |
| `anio` | Año del evento. | Derivado de `minuto_inicio`. |
| `mes` | Número de mes. | Derivado de `minuto_inicio`. |
| `dia` | Día del mes. | Derivado de `minuto_inicio`. |
| `hora` | Hora del día, de 0 a 23. | Derivada de `minuto_inicio`. |
| `minuto` | Minuto dentro de la hora. | Derivado de `minuto_inicio`. |
| `numero_dia_semana` | Número ISO del día de la semana. | Derivado de la fecha. |
| `dia_semana` | Nombre del día de la semana. | Derivado de la fecha. |
| `es_dia_habil` | Indica si el día corresponde de lunes a viernes. | Regla de negocio calculada en Gold. |
| `es_hora_pico` | Indica si el minuto corresponde a una franja de hora pico. | Verdadero entre 06:00–08:59 y 16:00–18:59. |

---

## 1.5 dim_punto_servicio

**Grano:** una fila por estación, parada o punto de servicio de los sistemas integrados.

**Origen:** catálogos de estaciones y paradas cargados en Bronze y procesados
durante Silver.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `punto_servicio_key` | Llave sustituta del punto de servicio. | Generada en Gold. |
| `modo_key` | Llave del modo de transporte al que pertenece el punto. | Relación con `dim_modo`. |
| `modo_codigo` | Código del sistema de transporte. | Valor conformado del operador. |
| `codigo_fuente` | Identificador original de estación o parada en la fuente. | Conservado desde los catálogos de origen. |
| `nombre` | Nombre descriptivo del punto de servicio. | Normalizado a partir del catálogo correspondiente. |
| `linea_ruta_eje` | Línea, ruta o eje asociado al punto de servicio. | Unificación de los conceptos equivalentes utilizados por cada operador. |
| `zona_key` | Llave de la zona donde se encuentra el punto. | Relación con `dim_zona`. |
| `zona_nombre` | Nombre conformado de la zona. | Obtenido mediante la conformación territorial realizada en Silver. |
| `latitud` | Latitud del punto cuando está disponible. | Conservada desde el catálogo de la fuente. |
| `longitud` | Longitud del punto cuando está disponible. | Conservada desde el catálogo de la fuente. |

---

## 1.6 fact_abordajes

**Grano:** una fila por evento de abordaje válido observado en la red integrada.

Esta tabla permite analizar de manera común los eventos de utilización de
Transmetro, Transurbano, Aerómetro y la entrada de los viajes de MetroRiel.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `abordaje_key` | Llave sustituta única del abordaje dentro de Gold. | Generada durante la construcción del hecho. |
| `usuario_key` | Usuario asociado al evento. | Relación con `dim_usuario`. |
| `modo_key` | Sistema de transporte donde ocurrió el evento. | Relación con `dim_modo`. |
| `tiempo_key` | Minuto en el que ocurrió el abordaje. | Relación con `dim_tiempo` a partir del timestamp normalizado en Silver. |
| `zona_key` | Zona donde ocurrió el abordaje. | Relación con `dim_zona`. |
| `punto_servicio_key` | Estación, parada o punto donde ocurrió el evento. | Relación con `dim_punto_servicio`. |
| `evento_id` | Identificador del evento en su sistema de origen. | Conserva el identificador operativo necesario para trazabilidad. |
| `cantidad_abordajes` | Medida aditiva utilizada para contar abordajes. | Valor 1 por cada evento válido incorporado al hecho. |
| `monto_gtq` | Monto asociado al evento expresado en quetzales. | Normalizado en Silver. En Transurbano el valor original en centavos se convierte a GTQ. |

### Consideración de MetroRiel

MetroRiel posee información de entrada y salida. Para análisis generales de
demanda se representa su entrada como un abordaje dentro de
`fact_abordajes`.

El recorrido completo se conserva adicionalmente en
`fact_viajes_metroriel`, evitando perder la información origen-destino.

---

## 1.7 fact_viajes_metroriel

**Grano:** una fila por viaje completo y válido de MetroRiel.

**Origen:** `silver.silver_metroriel_viajes`.

| Campo | Significado | Fuente / Transformación |
|---|---|---|
| `viaje_key` | Llave sustituta única del viaje dentro de Gold. | Generada durante la construcción del hecho. |
| `trip_id` | Identificador original del viaje MetroRiel. | Conservado desde Silver para trazabilidad. |
| `usuario_key` | Usuario asociado al viaje. | Relación con `dim_usuario`. |
| `modo_key` | Llave correspondiente a MetroRiel. | Relación con `dim_modo`. |
| `tiempo_entrada_key` | Minuto en que inicia el viaje. | Derivado de `fecha_hora_entrada_local` y relacionado con `dim_tiempo`. |
| `tiempo_salida_key` | Minuto en que termina el viaje. | Derivado de `fecha_hora_salida_local` y relacionado con `dim_tiempo`. |
| `zona_origen_key` | Zona donde inicia el viaje. | Relación con `dim_zona`. |
| `zona_destino_key` | Zona donde finaliza el viaje. | Relación con `dim_zona`. |
| `punto_origen_key` | Estación de entrada. | Relación con `dim_punto_servicio`. |
| `punto_destino_key` | Estación de salida. | Relación con `dim_punto_servicio`. |
| `cantidad_viajes` | Medida utilizada para contar viajes MetroRiel. | Valor 1 por cada viaje completo válido. |
| `tarifa_gtq` | Tarifa pagada por el viaje expresada en quetzales. | Normalizada en Silver. |
| `duracion_segundos` | Duración del recorrido entre entrada y salida. | Conservada y validada desde la fuente MetroRiel. |

---

## Consideración sobre nulabilidad

PostgreSQL puede reportar varios campos de Gold como técnicamente
nullable debido a que dbt no crea necesariamente restricciones físicas
`NOT NULL`.

La integridad de campos críticos se controla mediante pruebas dbt de
`not_null`, `unique` y pruebas de calidad personalizadas.

Por lo tanto, la nulabilidad física de PostgreSQL no sustituye las reglas
de calidad definidas para el proyecto.

---

# 2. Vistas analíticas de consumo

Las siguientes vistas se construyeron en la Fase 2 para facilitar el consumo
de la capa Gold desde Tableau.

No constituyen una nueva fuente de verdad. Sus campos se derivan de las
dimensiones y hechos del modelo dimensional principal.

---

## 2.1 vw_abordajes_analitica

**Grano:** una fila por abordaje válido de `fact_abordajes`.

**Objetivo:** exponer en una sola vista los atributos de usuario, modo,
tiempo, zona y punto de servicio necesarios para análisis en Tableau.

| Campo | Significado | Origen |
|---|---|---|
| `abordaje_key` | Llave única del abordaje en Gold. | `fact_abordajes.abordaje_key` |
| `evento_id` | Identificador del evento en el sistema de origen. | `fact_abordajes.evento_id` |
| `usuario_key` | Llave sustituta del usuario. | `dim_usuario.usuario_key` |
| `usuario_id` | Identificador seudonimizado y conformado del usuario. | `dim_usuario.usuario_id` |
| `cantidad_sistemas` | Número de sistemas donde se observa al usuario. | `dim_usuario.cantidad_sistemas` |
| `sistemas_observados` | Sistemas asociados a la identidad conformada. | `dim_usuario.sistemas_observados` |
| `es_multimodal_aprox` | Indica si la identidad aparece en más de un sistema enlazable. | `dim_usuario.es_multimodal_aprox` |
| `modo_key` | Llave sustituta del modo. | `dim_modo.modo_key` |
| `modo_codigo` | Código estandarizado del modo. | `dim_modo.modo_codigo` |
| `modo_nombre` | Nombre legible del modo. | `dim_modo.modo_nombre` |
| `tiempo_key` | Llave de tiempo asociada al abordaje. | `dim_tiempo.tiempo_key` |
| `minuto_inicio` | Inicio del minuto donde ocurrió el evento. | `dim_tiempo.minuto_inicio` |
| `fecha` | Fecha del evento. | `dim_tiempo.fecha` |
| `anio` | Año del evento. | `dim_tiempo.anio` |
| `mes` | Mes del evento. | `dim_tiempo.mes` |
| `dia` | Día del mes. | `dim_tiempo.dia` |
| `hora` | Hora del evento. | `dim_tiempo.hora` |
| `minuto` | Minuto del evento. | `dim_tiempo.minuto` |
| `numero_dia_semana` | Número ISO del día de semana. | `dim_tiempo.numero_dia_semana` |
| `dia_semana` | Nombre del día de semana. | `dim_tiempo.dia_semana` |
| `es_dia_habil` | Indica si el evento ocurrió de lunes a viernes. | `dim_tiempo.es_dia_habil` |
| `es_hora_pico` | Indica si el evento ocurrió en una franja definida como hora pico. | `dim_tiempo.es_hora_pico` |
| `zona_key` | Llave sustituta de la zona. | `dim_zona.zona_key` |
| `zona_nombre` | Nombre conformado de la zona. | `dim_zona.zona_nombre` |
| `punto_servicio_key` | Llave del punto de servicio. | `dim_punto_servicio.punto_servicio_key` |
| `codigo_fuente` | Código original de estación o parada. | `dim_punto_servicio.codigo_fuente` |
| `punto_servicio_nombre` | Nombre descriptivo del punto de servicio. | `dim_punto_servicio.nombre` |
| `linea_ruta_eje` | Línea, ruta o eje del punto de servicio. | `dim_punto_servicio.linea_ruta_eje` |
| `latitud` | Latitud del punto cuando está disponible. | `dim_punto_servicio.latitud` |
| `longitud` | Longitud del punto cuando está disponible. | `dim_punto_servicio.longitud` |
| `cantidad_abordajes` | Medida utilizada para contar abordajes. | `fact_abordajes.cantidad_abordajes` |
| `monto_gtq` | Monto asociado al abordaje expresado en quetzales. | `fact_abordajes.monto_gtq` |

---

## 2.2 vw_cobertura_zonas

**Grano:** una fila por zona conformada.

**Objetivo:** medir la cobertura disponible y relacionarla con la demanda
observada.

| Campo | Significado | Transformación |
|---|---|---|
| `zona_key` | Llave sustituta de la zona. | Heredada de `dim_zona`. |
| `zona_nombre` | Nombre conformado de la zona. | Heredado de `dim_zona`. |
| `cantidad_puntos_servicio` | Cantidad de estaciones, paradas o puntos disponibles en la zona. | Conteo de registros de `dim_punto_servicio`. |
| `cantidad_modos` | Número de modos distintos con presencia en la zona. | Conteo distinto de modos de `dim_punto_servicio`. |
| `modos_disponibles` | Lista de modos con presencia en la zona. | Agregación de nombres de `dim_modo`. |
| `nivel_cobertura` | Clasificación de la zona según cantidad de modos disponibles. | Derivado de `cantidad_modos`. |
| `tiene_servicio` | Indica si existe al menos un modo disponible en la zona. | Verdadero cuando `cantidad_modos > 0`. |
| `abordajes_totales` | Cantidad total de abordajes observados en la zona. | Suma de `fact_abordajes.cantidad_abordajes`. |
| `usuarios_distintos` | Cantidad de usuarios distintos observados en la zona. | Conteo distinto de `usuario_key` en `fact_abordajes`. |

---

## 2.3 vw_metroriel_demanda

**Grano:** una fila por zona conformada.

**Objetivo:** comparar la demanda territorial con las zonas que forman
parte del corredor propuesto de MetroRiel.

| Campo | Significado | Transformación |
|---|---|---|
| `zona_key` | Llave sustituta de la zona. | Heredada de `dim_zona`. |
| `zona_nombre` | Nombre conformado de la zona. | Heredado de `dim_zona`. |
| `abordajes_totales` | Total de abordajes observados en la zona. | Agregación de `fact_abordajes`. |
| `usuarios_distintos` | Cantidad de usuarios distintos observados en la zona. | Conteo distinto de `usuario_key`. |
| `pertenece_corredor_metroriel` | Indica si la zona pertenece al corredor evaluado. | Verdadero para Zonas 12, 8, 1, 6 y 17. |
| `ranking_demanda` | Posición de la zona según cantidad de abordajes. | `DENSE_RANK` descendente sobre `abordajes_totales`. |
| `porcentaje_demanda_total` | Porcentaje de la demanda total correspondiente a la zona. | `abordajes_totales / total de abordajes * 100`. |

---

## 2.4 vw_usuarios_multimodales

**Grano:** una fila por identidad conformada de usuario.

**Objetivo:** facilitar el análisis de utilización de múltiples sistemas.

| Campo | Significado | Transformación |
|---|---|---|
| `usuario_key` | Llave sustituta del usuario. | Heredada de `dim_usuario`. |
| `usuario_id` | Identificador seudonimizado del usuario. | Heredado de `dim_usuario`. |
| `cantidad_sistemas` | Cantidad de sistemas asociados al usuario. | Heredada de `dim_usuario`. |
| `sistemas_observados` | Lista de sistemas donde fue observada la identidad. | Heredada de `dim_usuario`. |
| `es_multimodal_aprox` | Indica si el usuario fue observado en más de un sistema enlazable. | Heredado de `dim_usuario`. |
| `identidad_aislada` | Indica que la identidad no posee enlace confiable con los demás operadores. | Heredado de `dim_usuario`. |
| `nivel_multimodalidad` | Clasificación legible según cantidad de sistemas o aislamiento de identidad. | Derivado de `cantidad_sistemas` e `identidad_aislada`. |

---

# 3. Principio de consumo de Gold

Las tablas dimensionales y de hechos constituyen la fuente oficial de
verdad analítica.

Las vistas `vw_*` son interfaces de consumo diseñadas para simplificar
Tableau y otras herramientas analíticas.

Las reglas de negocio deben definirse en el pipeline y no reconstruirse de
manera independiente dentro de Tableau.