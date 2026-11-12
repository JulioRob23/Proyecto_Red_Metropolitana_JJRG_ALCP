# Fase 2.2 - Estado congelado antes del test B

## Estado

**B NO EVALUADO**

En este punto el modelo, sus hiperparámetros y el umbral se encuentran
congelados utilizando únicamente información del corte A.

## Modelo seleccionado

- Modelo: HistGradientBoostingClassifier
- Versión: p2_hgb_v1
- learning_rate: 0.05
- max_iter: 150
- max_leaf_nodes: 15
- min_samples_leaf: 30
- l2_regularization: 1.0
- early_stopping: False
- random_state: 42

## Rendimiento de validación

- Métrica: Average Precision
- AP media: 0.478147
- AP std: 0.008159
- Validación cruzada: 5 folds del corte A

## Escenario económico

- Costo por contacto: Q5
- Retención si la persona iba a abandonar: 25%
- Valor de una persona retenida: Q60
- Beneficio esperado de contactar a una persona que iba a abandonar: Q15

La ganancia para un grupo contactado se calcula como:

`Ganancia = 15 × TP - 5 × (TP + FP)`

## Umbral

El umbral económico teórico fue:

`5 / 15 = 0.333333`

El umbral seleccionado mediante las predicciones OOF del corte A fue:

**0.341156**

Con este umbral en A:

- Contactados: 7,227
- Precision: 0.5009
- Recall: 0.4356
- Ganancia esperada: Q18,165.00

## Regla para el test

A partir de este punto no se modificarán las features, el modelo,
los hiperparámetros ni el umbral después de observar el resultado
del corte B.

La siguiente evaluación de B será la única evaluación de test del proyecto.
