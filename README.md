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

## Proyecto 2 - Ejecución desde cero

Para el Proyecto 2 se reutilizó y ajustó el pipeline construido en el
Proyecto 1. Los nuevos archivos se colocan en la carpeta `datos_red/`.

La ejecución completa desde un entorno limpio se realiza con un único
comando:

```powershell
python orchestration\flujo_proyecto2.py --desde-cero

---

# Proyecto 2 - Predicción de abandono

## Modelo final

El modelo final del Proyecto 2 es un `HistGradientBoostingClassifier` entrenado con el corte A.

El pipeline completo se encuentra en:

`models/modelo_churn_p2_hgb_v1.joblib`

El modelo no se reentrena dentro de `predecir.py`.

## Instalación reproducible

Crear y activar un entorno virtual con Python 3.11.

Luego instalar las dependencias exactas:

```powershell
pip install -r requirements-lock.txt
```

Crear el archivo `.env` tomando como referencia `.env.example`.

Levantar la infraestructura:

```powershell
docker compose up -d
```

## Predicción de producción

El comando oficial es:

```powershell
python predecir.py --datos <carpeta> --fecha-corte 2026-08-30
```

Este comando:

1. recibe la carpeta de datos;
2. ejecuta el pipeline de datos;
3. calcula las features utilizando únicamente información anterior a la fecha de corte;
4. carga el modelo versionado desde disco;
5. aplica el umbral congelado;
6. genera el CSV de producción.

El resultado se guarda en:

`predicciones/predicciones_corte_C.csv`

El archivo contiene las columnas:

`unidad_id, tarjetas, puntaje, contactar`

## Modo de desarrollo

Cuando la base de datos ya contiene correctamente las capas Silver, se puede evitar repetir toda la ingesta utilizando:

```powershell
python predecir.py `
  --datos .\datos_red `
  --fecha-corte 2026-08-30 `
  --usar-db-existente
```

Este modo se utiliza únicamente para desarrollo local.

El comando oficial de evaluación no requiere `--usar-db-existente`.

## Resultado entregado del corte C

Fecha de corte:

`2026-08-30`

Resultados:

- Población: 40,296
- Contactar: 5,480
- No contactar: 34,816
- Umbral: 0.341156328362
- Puntaje mínimo: 0.001621
- Puntaje máximo: 0.793317

SHA256 del CSV entregado:

`e7397c3d8e2a02f7f12640e1e497af3ba28b6f03f0102a1fc5db03d1b801e028`

## Modelo guardado

Archivo:

`models/modelo_churn_p2_hgb_v1.joblib`

Versión:

`p2_hgb_v1`

El archivo contiene el pipeline completo de preprocesamiento y el modelo `HistGradientBoostingClassifier`.

El modelo fue entrenado únicamente con el corte A y posteriormente guardado con `joblib`.

`predecir.py` carga este archivo directamente y no realiza entrenamiento nuevamente.

## Umbral de decisión

El escenario económico utilizado considera:

- costo por contacto: Q5;
- probabilidad de retener a un usuario que iba a abandonar: 25%;
- valor de un usuario retenido: Q60.

El punto de equilibrio teórico es:

`5 / (0.25 × 60) = 0.333333`

El umbral seleccionado utilizando las predicciones OOF del corte A fue:

`0.341156328362`

Este umbral quedó congelado antes de evaluar el corte B.

## Evaluación del modelo

La métrica principal utilizada fue `Average Precision`.

Resultados de validación cruzada en el corte A:

- Average Precision media: 0.478147
- Desviación estándar: 0.008159

Resultado de la única evaluación sobre el corte B:

- Average Precision: 0.651994
- Precision: 0.6399
- Recall: 0.7082
- TP: 10,711
- FP: 6,028
- TN: 33,126
- FN: 4,414
- Ganancia esperada: Q76,970

El corte B fue utilizado una única vez y no se utilizó posteriormente para reajustar el modelo.

## Prueba de invariancia

El archivo original de predicciones del corte C se conserva como:

`predicciones/predicciones_corte_C_baseline.csv`

Para comprobar invariancia se puede ejecutar:

```powershell
python modeling/fase2_4_bloque_c_invariancia.py
```

El resultado esperado es:

```text
RESULTADO: INVARIANCIA SUPERADA
```

En la prueba local se obtuvo:

- Filas baseline: 40,296
- Filas actuales: 40,296
- Mismas unidades: True
- Mismas tarjetas: True
- Mismos contactos: True
- Diferencia máxima del puntaje: 0.000000000000

SHA256 baseline:

`e7397c3d8e2a02f7f12640e1e497af3ba28b6f03f0102a1fc5db03d1b801e028`

SHA256 actual:

`e7397c3d8e2a02f7f12640e1e497af3ba28b6f03f0102a1fc5db03d1b801e028`

La prueba definitiva de invariancia se realizará durante la evaluación, cuando se reciban 30 días adicionales de información.

En ese momento se volverá a ejecutar:

```powershell
python predecir.py --datos <carpeta_nueva> --fecha-corte 2026-08-30
```

y posteriormente:

```powershell
python modeling/fase2_4_bloque_c_invariancia.py
```

Las predicciones del corte C deben permanecer exactamente iguales.

## Reproducibilidad

El proyecto utiliza:

- Python 3.11
- dbt Core
- dbt-postgres
- Prefect
- PostgreSQL
- Docker
- pandas
- scikit-learn
- joblib

Las versiones exactas utilizadas se encuentran en:

`requirements-lock.txt`

La semilla fija utilizada por los modelos es:

`random_state = 42`

## Ficha del modelo

La documentación completa del modelo se encuentra en:

`docs/proyecto2/fase2/ficha_modelo_p2.md`

Esta ficha incluye:

- datos y período;
- unidad de análisis;
- definición de población;
- definición de etiqueta;
- features utilizadas;
- modelo seleccionado;
- métricas de validación;
- resultado del corte B;
- umbral económico;
- controles de fuga;
- limitaciones;
- reproducibilidad;
- aviso de que los datos son simulados.

## Limitaciones

La integración de identidad entre operadores no es perfecta.

Aerómetro mantiene identidades aisladas cuando no existe un crosswalk confiable con los demás sistemas.

El modelo aprende patrones del período disponible y puede verse afectado por cambios de comportamiento en otros períodos.

Los costos utilizados para calcular el umbral corresponden a un escenario simulado con fines académicos.

Las relaciones encontradas por el modelo son predictivas y no deben interpretarse automáticamente como relaciones causales.