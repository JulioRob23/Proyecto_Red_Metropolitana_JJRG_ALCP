# Fase 2.1 - Ensemble y análisis sesgo-varianza

## Objetivo

En esta sección comparamos los modelos obtenidos en la Fase 1 con un modelo
ensemble, utilizando exactamente los mismos cinco folds estratificados del
corte A.

No se utilizó la etiqueta del corte B durante esta etapa.

## Ensemble seleccionado para comparación

Se utilizó `HistGradientBoostingClassifier` con la siguiente configuración:

- learning_rate = 0.05
- max_iter = 150
- max_leaf_nodes = 15
- min_samples_leaf = 30
- l2_regularization = 1.0
- early_stopping = False
- random_state = 42

La configuración se mantuvo fija durante los cinco folds.

## Comparación de modelos

| Modelo | AP entrenamiento | AP validación | AP std validación | Brecha train-validation |
|---|---:|---:|---:|---:|
| HistGradientBoosting | 0.507178 | 0.478147 | 0.008159 | 0.029031 |
| Logística L2 | 0.460862 | 0.460007 | 0.009004 | 0.000855 |
| Logística L1 | 0.460699 | 0.459745 | 0.009365 | 0.000954 |
| Baseline recencia | 0.444777 | 0.445212 | 0.008160 | -0.000435 |
| Baseline prevalencia | 0.138502 | 0.138502 | 0.000005 | aproximadamente 0 |

## Análisis de sesgo-varianza

### Baseline de prevalencia

Presenta un sesgo muy alto porque asigna el mismo puntaje a todas las personas
y no utiliza ninguna característica individual. Su resultado sirve únicamente
como referencia mínima.

### Baseline de recencia

Utiliza una señal individual importante y mejora ampliamente respecto al
baseline de prevalencia. Sin embargo, al utilizar únicamente una característica
su capacidad para representar patrones más complejos es limitada.

### Regresión logística L1

La diferencia entre entrenamiento y validación es muy pequeña, por lo que el
modelo presenta baja varianza. Su comportamiento es estable, aunque su
Average Precision se mantiene alrededor de 0.46, indicando una capacidad más
limitada para capturar relaciones no lineales.

### Regresión logística L2

También presenta una brecha muy pequeña entre entrenamiento y validación
(0.000855), por lo que tiene baja varianza y buen nivel de estabilidad. Fue
la mejor regresión logística, con AP de validación de 0.460007.

### HistGradientBoosting

El ensemble alcanzó una AP de entrenamiento de 0.507178 y una AP de validación
de 0.478147, para una brecha promedio de 0.029031.

Esta diferencia muestra que el ensemble presenta mayor varianza que las
regresiones logísticas, ya que logra ajustarse con mayor fuerza a los datos de
entrenamiento. Sin embargo, no observamos un sobreajuste severo porque el
rendimiento de validación también mejora y permanece estable entre los cinco
folds.

## Mejora respecto a la logística

La mejora absoluta frente a la mejor regresión logística fue:

0.478147 - 0.460007 = 0.018140 puntos de Average Precision.

Esto representa aproximadamente una mejora relativa del 3.9% respecto al
desempeño de validación de la logística L2.

Además, la desviación estándar en validación del ensemble fue 0.008159,
ligeramente menor que la de la logística L2, que fue 0.009004.

## Importancia por permutación

La importancia de variables se calculó exclusivamente sobre los conjuntos de
validación de los cinco folds.

La variable claramente más importante fue:

`dias_desde_ultimo_viaje`

Esto coincide con los resultados obtenidos anteriormente con el baseline de
recencia y con los coeficientes de la regresión logística.

Entre las siguientes variables más relevantes aparecieron:

- zona_mas_frecuente
- gasto_total_28d
- viajes_14d
- viajes_28d
- dias_activos_28d
- proporcion_metroriel
- proporcion_transurbano
- gasto_promedio_28d
- viajes_7d

La importancia por permutación indica cuánto disminuye Average Precision
cuando se destruye la información de una variable en validación. Por esta
razón, una mayor caída indica que la variable tiene mayor importancia para las
predicciones del modelo.

## Decisión

Seleccionamos `HistGradientBoostingClassifier` como modelo candidato para
producción.

Aunque presenta una mayor brecha entre entrenamiento y validación que la
regresión logística, mejora la Average Precision de validación de 0.460007 a
0.478147 y mantiene una desviación estándar similar.

La mejora observada justifica la complejidad adicional porque el costo
computacional sigue siendo bajo en nuestro conjunto de datos y el ensemble
captura relaciones no lineales que la regresión logística no representa de la
misma manera.

Esta decisión se tomó utilizando únicamente el corte A. La etiqueta del corte
B permanece sin utilizar y se reservará para la única evaluación final de la
sección 2.2.