# Ficha del modelo - Proyecto 2 Red Metropolitana

## Identificación

**Versión:** p2_hgb_v1  
**Modelo:** HistGradientBoostingClassifier  
**Unidad:** Persona (`usuario_id`)  
**Datos:** simulados con fines académicos.

## Datos y período

Los datos del Proyecto 2 cubren del 1 de junio al 29 de agosto de 2026.

El modelo utiliza una ventana máxima de 28 días anteriores a cada fecha de
corte.

Cortes utilizados:

- A: 2026-07-01 - entrenamiento y validación
- B: 2026-07-31 - test final utilizado una única vez
- C: 2026-08-30 - producción

## Población

Una persona pertenece a la población de un corte cuando registra al menos
dos abordajes válidos durante los 28 días anteriores al corte y no tiene un
DELETE del CDC aplicado antes de esa fecha.

## Etiqueta

La etiqueta vale 1 cuando una persona de la población no registra ningún
abordaje válido en ningún operador durante los 30 días que comienzan en la
fecha de corte, y vale 0 cuando registra al menos uno.

La etiqueta del corte C no está disponible.

## Features

El modelo utiliza 17 features relacionadas con:

- frecuencia de viajes en 7, 14 y 28 días;
- días activos;
- recencia;
- cantidad de modos y multimodalidad;
- modo y zona predominantes;
- hora pico y día hábil;
- gasto;
- proporción de utilización de cada operador.

Todas las features utilizan solamente información anterior a la fecha de
corte.

## Modelo seleccionado

Se seleccionó HistGradientBoostingClassifier con:

- learning_rate = 0.05
- max_iter = 150
- max_leaf_nodes = 15
- min_samples_leaf = 30
- l2_regularization = 1.0
- early_stopping = False
- random_state = 42

La decisión se tomó utilizando únicamente validación cruzada sobre el corte A.

## Rendimiento

Validación cruzada en A:

- Average Precision media: 0.478147
- Desviación estándar: 0.008159

Única evaluación en B:

- Average Precision: 0.651994
- Precision con el umbral congelado: 0.6399
- Recall: 0.7082
- TP: 10,711
- FP: 6,028
- TN: 33,126
- FN: 4,414

El corte B fue evaluado una sola vez y no se utilizó posteriormente para
ajustar el modelo.

## Umbral y costo

Escenario económico:

- Costo por contacto: Q5
- Probabilidad de retención de una persona que iba a abandonar: 25%
- Valor de una persona retenida: Q60

El punto de equilibrio teórico es:

`5 / (0.25 × 60) = 0.333333`

El umbral seleccionado mediante predicciones OOF del corte A fue:

**0.341156328362**

En el corte B este umbral produjo una ganancia esperada de:

**Q76,970**

## Producción - corte C

Fecha de corte:

**2026-08-30**

Resultados:

- Población: 40,296
- Contactar: 5,480
- No contactar: 34,816
- Puntaje mínimo: 0.001621
- Puntaje máximo: 0.793317

El archivo de producción es:

`predicciones/predicciones_corte_C.csv`

SHA256 original:

`e7397c3d8e2a02f7f12640e1e497af3ba28b6f03f0102a1fc5db03d1b801e028`

## Controles de fuga

Las features utilizan solamente eventos anteriores a la fecha de corte y
mantienen ventanas máximas de 28 días.

La auditoría del corte A comparó las features construidas con los datos
completos contra los datos recortados al 30 de junio. Las 59,999 filas fueron
idénticas y se obtuvieron 0 diferencias.

El corte B se utilizó una única vez después de congelar el modelo y el umbral.

Se preparó además una prueba de invariancia para comprobar que las
predicciones del corte C no cambien al incorporar datos posteriores al
30 de agosto.

La prueba local de control produjo 0 diferencias y SHA256 idénticos. La
prueba definitiva se realizará con los 30 días adicionales suministrados
durante la evaluación.

## Limitaciones

La integración de identidad entre operadores no es perfecta. Aerómetro
mantiene identidades aisladas cuando no existe un crosswalk confiable.

El modelo aprende patrones del período disponible y puede verse afectado por
cambios de comportamiento en otros períodos.

El valor económico utilizado es un escenario simulado y no representa costos
reales de una agencia de transporte.

Las tasas de abandono y las relaciones observadas son predictivas y no deben
interpretarse automáticamente como relaciones causales.

## Reproducibilidad

El pipeline completo está guardado en:

`models/modelo_churn_p2_hgb_v1.joblib`

El archivo contiene tanto el preprocesamiento como el
HistGradientBoostingClassifier y `predecir.py` lo carga sin reentrenarlo.

Semilla utilizada:

`random_state = 42`