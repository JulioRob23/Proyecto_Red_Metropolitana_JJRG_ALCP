# Linaje y Trazabilidad de Datos

## Objetivo

El linaje permite identificar el origen de una métrica y recorrer el camino
desde el resultado analítico hasta la fuente original.

El proyecto utiliza dos niveles de trazabilidad:

1. Linaje de ingestión: desde los archivos originales hasta Bronze y Staging.
2. Linaje dbt: desde las fuentes registradas en PostgreSQL hasta Silver,
   Gold y las vistas analíticas.

---

# 1. Linaje general

Fuentes operacionales
→ Ingesta
→ Bronze
→ Staging
→ modelos Staging dbt
→ Silver
→ Gold
→ vistas analíticas
→ Tableau

Los registros inválidos detectados durante la transformación hacia Silver
se conservan adicionalmente en cuarentena.

---

# 2. Linaje por operador

## Transmetro

`transmetro_validaciones.csv`

→ ingesta Streaming mediante Kafka

→ `lake/bronze/transmetro/`

→ Staging operacional

→ `stg_transmetro`

→ `silver.silver_transmetro_validaciones`

→ `gold.fact_abordajes`

→ `gold.vw_abordajes_analitica`

→ Tableau

El padrón de usuarios de Transmetro utiliza adicionalmente CDC para mantener
el estado vigente y la historia SCD Tipo 2 utilizada durante la integración
de identidad.

---

## Transurbano

`transurbano_transacciones.csv`

→ ingesta Streaming mediante Kafka

→ `lake/bronze/transurbano/`

→ Staging operacional

→ `stg_transurbano`

→ `silver.silver_transurbano_transacciones`

→ `gold.fact_abordajes`

→ `gold.vw_abordajes_analitica`

→ Tableau

---

## MetroRiel

`metroriel_viajes.jsonl`

→ ingesta Batch

→ `lake/bronze/metroriel/`

→ Staging operacional

→ `stg_metroriel`

→ `silver.silver_metroriel_viajes`

→ dos usos en Gold:

1. Entrada del viaje
   → `gold.fact_abordajes`
   → `gold.vw_abordajes_analitica`

2. Viaje completo
   → `gold.fact_viajes_metroriel`

→ Tableau y análisis de movilidad.

---

## Aerómetro

`aerometro_boardings.csv`

→ ingesta Streaming mediante Kafka

→ `lake/bronze/aerometro/`

→ Staging operacional

→ `stg_aerometro`

→ `silver.silver_aerometro_boardings`

→ `gold.fact_abordajes`

→ `gold.vw_abordajes_analitica`

→ Tableau

---

# 3. Catálogos

Los catálogos de puntos de servicio siguen el flujo:

archivos de catálogo

→ ingesta Batch

→ Bronze

→ Staging

→ modelos dbt Staging

→ dimensiones conformadas de Gold.

Los archivos principales son:

- `tm_estaciones.csv`
- `tu_paradas.csv`
- `mr_estaciones.csv`
- `am_estaciones.csv`

Estos datos alimentan principalmente:

- `gold.dim_punto_servicio`
- `gold.dim_zona`
- `gold.dim_modo`

---

# 4. Linaje de las métricas del tablero

## Abordajes totales

Tableau

→ `gold.vw_abordajes_analitica.cantidad_abordajes`

→ `gold.fact_abordajes.cantidad_abordajes`

→ modelos Silver de los cuatro operadores

→ eventos originales en Bronze

→ archivos operacionales originales.

La definición oficial es:

`SUM(cantidad_abordajes)`

---

## Demanda por zona

Tableau

→ `gold.vw_abordajes_analitica`

→ `gold.fact_abordajes`

+ `gold.dim_zona`

→ Silver

→ Staging

→ Bronze

→ fuentes originales.

---

## Hora pico

Tableau

→ `gold.vw_abordajes_analitica.es_hora_pico`

→ `gold.dim_tiempo.es_hora_pico`

→ regla oficial de tiempo definida en Gold.

La definición utilizada es:

- 06:00–08:59
- 16:00–18:59

---

## Cobertura

Tableau

→ `gold.vw_cobertura_zonas`

→ `gold.dim_punto_servicio`

+ `gold.dim_zona`

+ `gold.dim_modo`

→ catálogos procesados desde Silver/Staging

→ archivos de estaciones y paradas.

---

## Multimodalidad

Tableau

→ `gold.vw_usuarios_multimodales`

→ `gold.dim_usuario`

→ puente de identidad construido en Silver

→ identificadores seudonimizados de los operadores.

La métrica representa multimodalidad aproximada y no confirma transbordos
físicos.

---

## Corredor MetroRiel

Tableau

→ `gold.vw_metroriel_demanda`

→ demanda agregada de `gold.fact_abordajes`

+ `gold.dim_zona`

→ capas Silver correspondientes

→ fuentes originales.

---

# 5. Linaje de features

La tabla:

`features.features_usuario`

no utiliza Gold como entrada.

Su linaje es:

Silver
→ `features.int_eventos_usuario_features`
→ `features.features_usuario`

Esto se decidió porque el feature engineering necesita conservar el detalle
temporal a nivel de usuario antes de la agregación analítica realizada para
otros consumidores.

---

# 6. Regla arquitectónica

Gold nunca debe consumir directamente Bronze.

El flujo obligatorio es:

Bronze
→ Staging
→ Silver
→ Gold

La separación garantiza que los datos analíticos hayan pasado por las
reglas de limpieza, integración, normalización y calidad antes de utilizarse
para decisiones.

---

# 7. Reproducibilidad del linaje

El grafo técnico de dependencias dbt puede regenerarse mediante:

`dbt docs generate --project-dir dbt`

y visualizarse mediante:

`dbt docs serve --project-dir dbt --port 8081`

Por tanto, el linaje no depende únicamente de documentación manual; también
se deriva de las dependencias `source()` y `ref()` implementadas en los
modelos dbt.

---

# Matriz resumida de trazabilidad

| Resultado | Fuente analítica | Fuente integrada | Origen |
|---|---|---|---|
| Demanda total | `vw_abordajes_analitica` | `fact_abordajes` | Eventos de los cuatro operadores |
| Demanda por zona | `vw_abordajes_analitica` | `fact_abordajes` + `dim_zona` | Eventos + catálogos |
| Hora pico | `vw_abordajes_analitica` | `fact_abordajes` + `dim_tiempo` | Timestamps de eventos |
| Cobertura | `vw_cobertura_zonas` | `dim_punto_servicio` | Catálogos de estaciones/paradas |
| Multimodalidad | `vw_usuarios_multimodales` | `dim_usuario` | Puente de identidad Silver |
| Evaluación MetroRiel | `vw_metroriel_demanda` | `fact_abordajes` + `dim_zona` | Red integrada |