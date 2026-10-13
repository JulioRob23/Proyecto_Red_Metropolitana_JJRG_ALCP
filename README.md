# Proyecto Red Metropolitana

## Descripción

Este proyecto implementa una plataforma de datos para integrar información
de cuatro sistemas de transporte de la Red Metropolitana:

- Transmetro
- Transurbano
- MetroRiel
- Aerómetro

La solución integra datos provenientes de procesos Batch, Streaming y CDC,
los almacena mediante una arquitectura por capas y posteriormente los utiliza
para análisis en Tableau y para la construcción de una tabla de features
orientada a futuros modelos de ciencia de datos.

El proyecto fue desarrollado en tres fases:

- Fase 1: integración, calidad, Silver, Gold y orquestación.
- Fase 2: análisis en Tableau, recomendación y feature engineering.
- Fase 3: gobernanza, reproducibilidad y seguridad.

---

## Arquitectura general

El flujo principal del proyecto es:

Fuentes
   ↓
Ingesta Batch / Streaming / CDC
   ↓
Bronze
   ↓
Staging
   ↓
Silver
   ↓
Gold
   ↓
Tableau
   ↓
Recomendación


Desde Silver también se construye:

Silver
   ↓
Features
   ↓
Futuros modelos de ciencia de datos

Los registros que incumplen las reglas de calidad no se eliminan
silenciosamente. Estos registros se conservan en cuarentena para mantener
trazabilidad y permitir auditoría o reprocesamiento.

---

## Tecnologías utilizadas

- Python 3.11
- PostgreSQL
- Docker Desktop
- Docker Compose
- Apache Kafka
- dbt Core
- dbt-postgres
- Prefect
- Pandas
- PyArrow
- Tableau Desktop
- Git
- GitHub
- Visual Studio Code
- PowerShell

---

## Estructura principal del proyecto

Proyecto_Red_Metropolitana/
│
├── datos/
│   ├── generador/
│   └── raw/
│
├── ingestion/
│   ├── batch/
│   ├── streaming/
│   └── cdc/
│
├── lake/
│   └── bronze/
│
├── staging/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── silver/
│   │   ├── quarantine/
│   │   ├── gold/
│   │   └── features/
│   ├── tests/
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── orchestration/
│
├── sql/
│   ├── ddl/
│   └── queries/
│
├── tableau/
│
├── docs/
│   ├── decisiones/
│   ├── metricas/
│   ├── fase2/
│   └── fase3/
│
├── evidence/
│   ├── fase1/
│   ├── fase2/
│   └── fase3/
│
├── docker-compose.yml
├── requirements.txt
└── README.md

---

## Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.11
- Docker Desktop
- Git
- PowerShell
- Visual Studio Code
- Tableau Desktop para la visualización

---

## Preparación del entorno

### Activar el entorno virtual existente

Desde la raíz del proyecto:

.\.venv\Scripts\Activate.ps1

Cuando el entorno esté activo, la terminal debe mostrar:

(.venv)

### Salir del entorno virtual

deactivate

### Instalar dependencias

Si el proyecto se configura desde cero:

pip install -r requirements.txt

---

## Levantar la infraestructura

Abrir Docker Desktop y ejecutar desde la raíz del proyecto:

docker compose up -d

Verificar los servicios:

docker compose ps

Los componentes principales son:

- PostgreSQL
- Apache Kafka

PostgreSQL se encuentra disponible localmente mediante:


localhost:5433

---

## Configuración de dbt

El archivo `profiles.yml` se encuentra dentro de la carpeta `dbt`.

En cada nueva sesión de PowerShell se debe configurar:

$env:DBT_PROFILES_DIR = (Resolve-Path .\dbt).Path

Después se puede verificar la conexión:

dbt debug --project-dir dbt

El resultado esperado es:

All checks passed!

---

## Ejecución del pipeline principal

La Fase 1 cuenta con un flujo orquestado mediante Prefect.

Ejecutar:

python orchestration\flujo_fase1.py

El flujo coordina las principales etapas de:

Infraestructura
↓
Ingesta
↓
Staging
↓
Transformaciones dbt
↓
Pruebas
↓
Métricas

Además registra tiempos de ejecución por etapa.

---

## Ejecución manual de dbt

Ejecutar todos los modelos:


dbt run --project-dir dbt


Ejecutar todas las pruebas:


dbt test --project-dir dbt


Generar documentación y linaje:

dbt docs generate --project-dir dbt


Abrir la documentación:


dbt docs serve --project-dir dbt --port 8081

---

## Capas de datos

### Bronze

Bronze conserva los datos ingeridos en formato Parquet junto con información
de trazabilidad.

Entre los campos técnicos utilizados se encuentran:

- archivo de origen;
- fecha de ingesta;
- hash del archivo;
- número de fila cuando aplica.

Bronze funciona como histórico acumulativo y no se modifica para corregir
problemas de calidad.

### Staging

Staging funciona como una zona operacional temporal.

Su propósito es hacer disponibles los datos para las transformaciones dbt.
Puede vaciarse y reconstruirse porque el histórico oficial permanece en
Bronze.

### Silver

Silver contiene datos:

- limpios;
- normalizados;
- integrados;
- validados.

Las reglas de calidad se aplican antes del consumo analítico.

Los registros inválidos se conservan en cuarentena.

### Gold

Gold contiene el modelo dimensional oficial utilizado para análisis.

Incluye:


dim_modo
dim_zona
dim_usuario
dim_tiempo
dim_punto_servicio
fact_abordajes
fact_viajes_metroriel


Además contiene vistas analíticas utilizadas por Tableau:


vw_abordajes_analitica
vw_cobertura_zonas
vw_usuarios_multimodales
vw_metroriel_demanda


### Features

La capa Features contiene una tabla model-ready con una fila por usuario.

Incluye variables relacionadas con:

- actividad;
- recencia;
- cantidad de modos;
- multimodalidad aproximada;
- modo principal;
- zona frecuente;
- hora pico;
- día hábil;
- gasto.

---

## Tableau

El workbook principal se encuentra en:


tableau/Red_Metropolitana_Fase2.twb


Tableau utiliza una conexión Live a PostgreSQL y consume las vistas
analíticas de Gold.

Se construyeron dos dashboards principales:

1. Red Metropolitana - Demanda y Cobertura.
2. Red Metropolitana - Integración y MetroRiel.

---

## Resultados principales

Durante el período analizado se observaron:

| Indicador | Resultado |
|---|---:|
| Abordajes totales | 1,688,959 |
| Transurbano | 827,788 |
| Transmetro | 362,106 |
| MetroRiel | 295,511 |
| Aerómetro | 203,554 |
| Demanda en hora pico | 49.68% |
| Usuarios multimodales aproximados | 52.33% |
| Demanda en corredor MetroRiel | 43.41% |
| Zonas sin servicio observado | 1 |

---

## Calidad de datos

Los registros inválidos se conservan en cuarentena.

Las reglas principales implementadas son:

| Regla | Descripción general | Cantidad |
|---|---|---:|
| `QC01_TM_DUPLICADO` | Duplicados de Transmetro | 1,115 |
| `QC02_TU_PARADA_NULA` | Parada nula de Transurbano | 4,189 |
| `QC03_TU_FECHA_FUTURA` | Fecha futura de Transurbano | 817 |
| `QC04_MR_SIN_SALIDA` | Viaje MetroRiel sin salida válida | 3,589 |
| **Total** | Registros en cuarentena | **9,710** |

---

## Gobernanza

La documentación de gobernanza se encuentra en:


docs/fase3/gobernanza/


Incluye:

- inventario de Gold;
- diccionario de datos;
- definiciones oficiales;
- dueños por dominio;
- reglas de calidad;
- linaje y trazabilidad.

---

## Reproducibilidad

El proyecto utiliza:

- Git para versionar cambios;
- dbt para dependencias, pruebas y linaje;
- Prefect para orquestación;
- Docker para infraestructura reproducible.

Una ejecución correcta debe mantener:

Pruebas dbt sin errores
Conteos estables
Gold alimentado desde capas validadas
Features reproducibles
Ausencia de credenciales sensibles en Git


---

## Documentación adicional

Las decisiones técnicas se encuentran principalmente en:


docs/decisiones/
docs/fase2/
docs/fase3/


Las evidencias se encuentran en:


evidence/fase1/
evidence/fase2/
evidence/fase3/

---

## Limitaciones principales

La integración de identidad entre operadores es aproximada.

Aerómetro mantiene identidades aisladas debido a que no existe un crosswalk
confiable con los demás sistemas.

La multimodalidad indica utilización de varios sistemas, pero no confirma
un transbordo físico.

El período de datos disponible comprende aproximadamente del 1 de junio
al 15 de julio de 2026.