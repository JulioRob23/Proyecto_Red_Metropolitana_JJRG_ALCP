# Fase 2.2 - Única evaluación del corte B

## Registro

- Fecha de evaluación: 2026-11-11T22:45:37.393109-06:00
- Commit de congelamiento pre-test: `e8ae9366345c61fccb82e65519533bf00fe450c8`
- Commit del código de evaluación: `ae48cb2647e8fc06012ee33856b3b5ce6d59a1fe`
- Modelo: HistGradientBoostingClassifier
- Umbral congelado: 0.341156328362

## Resultados de validación A

- Average Precision CV A: 0.478147

## Resultados del test B

- Población B: 54,279
- Positivos B: 15,125
- Tasa positiva B: 0.2787
- Average Precision B: 0.651994
- Diferencia AP B - CV A: 0.173847

## Decisión con umbral congelado

- Umbral: 0.341156
- Contactados: 16,739
- TP: 10,711
- FP: 6,028
- TN: 33,126
- FN: 4,414
- Precision: 0.6399
- Recall: 0.7082

## Resultado económico

- Retenidos esperados: 2677.75
- Costo total: Q83,695.00
- Beneficio esperado: Q160,665.00
- Ganancia esperada en B: Q76,970.00

## Regla posterior al test

El corte B fue utilizado una única vez. No se modificarán el modelo,
las features, los hiperparámetros ni el umbral después de observar
este resultado.
