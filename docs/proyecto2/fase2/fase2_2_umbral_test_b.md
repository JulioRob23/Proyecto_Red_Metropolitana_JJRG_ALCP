# Fase 2.2 - Umbral según costo y test único

## Escenario económico

La Agencia definió los siguientes valores:

- Costo por contacto: Q5
- Probabilidad de retención si la persona iba a abandonar: 25%
- Valor de una persona retenida: Q60

El beneficio esperado de contactar a una persona que realmente iba a
abandonar es:

0.25 × Q60 = Q15

Por lo tanto, para una persona con probabilidad de abandono p:

Ganancia esperada = 15p - 5

El punto de equilibrio teórico es:

15p - 5 = 0

p = 5 / 15 = 0.333333

## Selección del umbral

El umbral definitivo no se eligió utilizando el corte B.

Se utilizaron exclusivamente las predicciones OOF de los cinco folds del
corte A.

El máximo de ganancia se obtuvo con:

- Umbral: 0.341156
- Contactados: 7,227
- TP: 3,620
- FP: 3,607
- Precision: 0.5009
- Recall: 0.4356
- Ganancia esperada: Q18,165

Este valor fue congelado antes de observar la etiqueta del corte B.

## Estado previo al test

Modelo congelado:

HistGradientBoostingClassifier

Configuración:

- learning_rate = 0.05
- max_iter = 150
- max_leaf_nodes = 15
- min_samples_leaf = 30
- l2_regularization = 1.0
- early_stopping = False
- random_state = 42

Commit de congelamiento:

e8ae9366345c61fccb82e65519533bf00fe450c8

Commit del código de evaluación:

ae48cb2647e8fc06012ee33856b3b5ce6d59a1fe

## Única evaluación del corte B

La evaluación se realizó una única vez el 11 de noviembre de 2026.

Resultados:

- Población: 54,279
- Positivos: 15,125
- Tasa positiva: 0.2787
- Average Precision: 0.651994
- Umbral: 0.341156
- Contactados: 16,739
- Precision: 0.6399
- Recall: 0.7082

Matriz de confusión:

- TN: 33,126
- FP: 6,028
- FN: 4,414
- TP: 10,711

## Resultado económico

Retenidos esperados:

10,711 × 0.25 = 2,677.75

Costo de campaña:

16,739 × Q5 = Q83,695

Beneficio esperado:

10,711 × Q15 = Q160,665

Ganancia:

Q160,665 - Q83,695 = Q76,970

Por lo tanto, la ganancia esperada de aplicar la decisión del modelo sobre
el corte B es Q76,970.

## Interpretación

El Average Precision de B fue superior al promedio de validación cruzada de
A. Esto no se utilizó para modificar el modelo ni el umbral.

Además, la proporción de positivos aumentó de aproximadamente 13.85% en A a
27.87% en B, por lo que la distribución de la población cambió entre ambos
cortes. Este cambio también debe considerarse al interpretar la diferencia
entre las métricas.

Después de esta evaluación no se modificaron las features, los
hiperparámetros, el modelo ni el umbral.