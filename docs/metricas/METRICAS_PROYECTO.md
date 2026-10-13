# Métricas Finales - Proyecto Red Metropolitana

## Objetivo

Este documento consolida las principales métricas medidas durante el
desarrollo del proyecto.

Las métricas provienen de ejecuciones reales del pipeline, consultas sobre
PostgreSQL, pruebas dbt, registros de Prefect y análisis en Tableau.

---

## 1. Volumen de datos

### Bronze

La capa Bronze recibió un total de:

**1,730,184 registros**

Distribuidos principalmente en:

| Fuente | Registros |
|---|---:|
| Transmetro | 363,221 |
| Transurbano | 832,791 |
| MetroRiel | 299,100 |
| Aerómetro | 203,554 |
| CDC padrón | 31,050 |
| Catálogos | 468 |
| **Total** | **1,730,184** |

Bronze conserva además metadatos de trazabilidad como archivo de origen,
fecha de ingesta y hash.

---

## 2. Volumen después de calidad e integración

Las tablas Silver principales contienen:

| Fuente | Registros Silver |
|---|---:|
| Transmetro | 362,106 |
| Transurbano | 827,788 |
| MetroRiel | 295,511 |
| Aerómetro | 203,554 |

Las cuatro fuentes principales suman:

**1,688,959 eventos válidos**

---

## 3. Calidad de datos

Se detectaron y conservaron en cuarentena:

| Regla | Cantidad |
|---|---:|
| QC01_TM_DUPLICADO | 1,115 |
| QC02_TU_PARADA_NULA | 4,189 |
| QC03_TU_FECHA_FUTURA | 817 |
| QC04_MR_SIN_SALIDA | 3,589 |
| **Total cuarentena** | **9,710** |

Después de aplicar las reglas, las claves principales de los cuatro
conjuntos Silver presentan:

**0 duplicados**

Los registros inválidos no fueron eliminados del histórico original.

---

## 4. CDC del padrón Transmetro

Se procesaron:

**31,050 eventos CDC**

Distribuidos en:

| Operación | Eventos |
|---|---:|
| INSERT | 10,800 |
| UPDATE | 16,200 |
| DELETE | 4,050 |

Para Transmetro se construyó un padrón vigente con:

| Estado | Usuarios |
|---|---:|
| Activos | 15,096 |
| Inactivos | 2,336 |
| **Total vigente** | **17,432** |

La representación SCD Tipo 2 contiene:

**22,326 versiones históricas**

para:

**17,432 tarjetas distintas**

---

## 5. Capa Gold

El modelo dimensional principal contiene:

| Relación | Filas |
|---|---:|
| dim_modo | 4 |
| dim_zona | 16 |
| dim_usuario | 70,380 |
| dim_tiempo | 64,800 |
| dim_punto_servicio | 468 |
| fact_abordajes | 1,688,959 |
| fact_viajes_metroriel | 295,511 |

Las claves dimensionales de las tablas de hechos fueron verificadas sin
valores nulos en los campos obligatorios definidos por el proyecto.

---

## 6. Demanda observada

La demanda total oficial es:

**1,688,959 abordajes**

Distribuidos en:

| Modo | Abordajes |
|---|---:|
| Transurbano | 827,788 |
| Transmetro | 362,106 |
| MetroRiel | 295,511 |
| Aerómetro | 203,554 |

La misma cifra total fue reproducida desde `fact_abordajes` y desde
`vw_abordajes_analitica`.

---

## 7. Demanda temporal

Se observó:

| Tipo de horario | Abordajes | Porcentaje |
|---|---:|---:|
| Hora pico | 839,033 | 49.68% |
| Fuera de hora pico | 849,926 | 50.32% |

Las franjas definidas como hora pico son:

- 06:00 a 08:59
- 16:00 a 18:59

---

## 8. Cobertura territorial

El modelo territorial contiene:

**16 zonas conformadas**

De ellas:

- 15 presentan servicio observado.
- 1 no presenta servicio observado.

La zona sin servicio dentro de los cuatro sistemas integrados es:

**Santa Catarina Pinula**

La ausencia de servicio observado no significa necesariamente ausencia de
necesidad de movilidad.

---

## 9. Multimodalidad

La dimensión de usuarios contiene:

**70,380 identidades**

De ellas:

**36,829 usuarios multimodales aproximados**

equivalentes a:

**52.33%**

Distribución por nivel:

| Nivel | Usuarios |
|---|---:|
| 2 sistemas | 26,833 |
| 1 sistema | 19,055 |
| Identidad aislada | 14,496 |
| 3 sistemas | 9,996 |

La multimodalidad representa presencia de una identidad en varios sistemas
y no confirma un transbordo físico.

---

## 10. Evaluación del corredor MetroRiel

Las cinco zonas con mayor demanda observada son:

1. Zona 17
2. Zona 12
3. Zona 8
4. Zona 6
5. Zona 1

Estas cinco zonas corresponden al corredor MetroRiel evaluado.

El corredor concentra:

**733,182 abordajes**

equivalentes a:

**43.41% de la demanda total**

Fuera del corredor se observan:

**955,777 abordajes**

equivalentes a:

**56.59%**

---

## 11. Features

La tabla:

`features.features_usuario`

contiene:

**70,380 filas**

y:

**70,380 usuarios distintos**

Por lo tanto:

**0 duplicados de usuario**

Promedios observados:

| Métrica | Resultado |
|---|---:|
| Eventos últimos 7 días | 3.76 |
| Eventos últimos 30 días | 16.09 |
| Eventos período completo | 24.00 |
| Cantidad promedio de modos | 1.67 |
| Porcentaje multimodal aproximado | 52.33% |

---

## 12. Rendimiento del pipeline

Se midieron dos ejecuciones completas mediante Prefect.

### Ejecución 1

Tiempo total:

**2,114.48 segundos**

### Ejecución 2

Tiempo total:

**2,195.33 segundos**

Las etapas de mayor duración fueron principalmente:

- Streaming de Transurbano.
- ejecución de modelos dbt;
- Streaming de Transmetro;
- Streaming de Aerómetro;
- construcción de Staging.

---

## 13. Rendimiento Tableau

Mediante Performance Recording se observaron consultas cuyo mayor tiempo
registrado durante la muestra fue aproximadamente:

**13.46 segundos**

Este valor corresponde al máximo observado durante la prueba realizada y
no debe interpretarse como tiempo promedio general del dashboard.

---

## 14. Idempotencia

El pipeline completo fue ejecutado nuevamente sobre los mismos archivos.

Los conteos de Bronze, Silver, Gold y cuarentena permanecieron sin cambios.

Resultado:

**Idempotencia verificada**

Esto demuestra que repetir la ejecución sobre las mismas entradas no genera
duplicación de información.

---

## 15. Pruebas automatizadas

Al cierre del bloque de gobernanza de la Fase 3 se ejecutaron:

**91 pruebas dbt**

Resultado:

PASS = 91
WARN = 0
ERROR = 0
SKIP = 0
TOTAL = 91

---

## Conclusión

Las métricas demuestran que la plataforma no solamente funciona a nivel
técnico, sino que cuenta con mediciones verificables de volumen, calidad,
CDC, rendimiento, idempotencia, cobertura, integración y consumo analítico.