# Fase 1.4 - Baseline y regresión logística regularizada

## Datos utilizados

Para esta fase utilizamos únicamente el corte A, correspondiente al
1 de julio de 2026.

La población contiene 59,999 personas:

- Positivos: 8,310
- Negativos: 51,689
- Tasa positiva: 8,310 / 59,999 = 0.1385

No utilizamos la etiqueta del corte B para entrenar, seleccionar variables,
elegir hiperparámetros ni comparar modelos.

## Métrica elegida

Elegimos Average Precision (AP) como métrica principal porque la clase de
abandono representa solamente el 13.85% de la población del corte A.

En este problema nos interesa identificar y ordenar correctamente a las
personas con mayor riesgo de abandono, en lugar de solamente maximizar el
porcentaje total de predicciones correctas.

Average Precision permite evaluar los puntajes o probabilidades de riesgo y
es apropiada cuando la clase positiva es minoritaria.

## Validación cruzada

Utilizamos validación cruzada estratificada de 5 folds con semilla fija 42.

Los mismos folds fueron utilizados para todos los modelos, de manera que la
comparación sea justa. Cada fold mantiene aproximadamente la misma tasa
positiva de 13.85%.

## Baselines

### Baseline 1 - Prevalencia

A todas las personas se les asignó la misma probabilidad:

8,310 / 59,999 = 0.1385

Este modelo representa el caso en que no conocemos ninguna característica
individual y únicamente utilizamos la proporción promedio de abandono.

Resultado:

- AP media: 0.138502
- AP std: 0.000005

### Baseline 2 - Recencia

Como segundo baseline utilizamos únicamente `dias_desde_ultimo_viaje` como
puntaje de riesgo, sin entrenar ningún modelo.

La lógica utilizada fue que una mayor cantidad de días desde el último viaje
representa mayor riesgo de abandono.

Resultado:

- AP media: 0.445212
- AP std: 0.008160

Este resultado muestra que la recencia por sí sola contiene bastante
información relacionada con el abandono.

## Regresión logística regularizada

Se compararon dos tipos de regularización:

- L1
- L2

Para ambos modelos se probaron los valores:

- λ = 0.01
- λ = 0.1
- λ = 1
- λ = 10
- λ = 100

En `LogisticRegression`, se utilizó la relación:

C = 1 / λ

La selección de λ se realizó únicamente mediante validación cruzada sobre
el corte A.

## Resultados

| Modelo | Configuración | AP media | AP std |
|---|---|---:|---:|
| Logística L2 | λ = 100, C = 0.01 | 0.460007 | 0.009004 |
| Logística L1 | λ = 10, C = 0.1 | 0.459745 | 0.009365 |
| Baseline recencia | dias_desde_ultimo_viaje | 0.445212 | 0.008160 |
| Baseline prevalencia | p = 8310 / 59999 | 0.138502 | 0.000005 |

La regresión logística L2 obtuvo el mayor Average Precision promedio con
0.460007.

La diferencia entre L1 y L2 es pequeña, por lo que no podemos decir que L2
sea ampliamente superior. Sin embargo, L2 obtuvo tanto una media ligeramente
mayor como una desviación estándar ligeramente menor.

Por esta razón seleccionamos como mejor configuración de regresión logística:

- Penalización: L2
- λ: 100
- C: 0.01
- AP media: 0.460007
- AP std: 0.009004

La logística L2 supera al baseline de recencia en aproximadamente 0.0148
puntos de Average Precision, mostrando que las demás características agregan
información adicional a la recencia.

## Comportamiento frente a λ

Las curvas de L1 y L2 se mantienen relativamente estables para la mayoría
de valores de λ.

En L1, el desempeño disminuye cuando λ llega a 100, lo que indica que una
regularización demasiado fuerte empieza a eliminar o reducir información útil.

En L2, el mejor resultado se obtiene con λ = 100. Aunque la mejora es pequeña,
esta configuración produce la mayor AP media observada.

Las barras de error representan la desviación estándar entre los cinco folds.
La variación entre folds es mayor que las diferencias observadas entre varios
valores de λ, lo que explica que las líneas de la gráfica se vean casi planas.

## Coeficientes que más empujan hacia el abandono

Los cinco coeficientes positivos más altos del mejor modelo fueron:

| Feature | Coeficiente |
|---|---:|
| dias_desde_ultimo_viaje | 0.732171 |
| zona_mas_frecuente_Zona 13 | 0.234181 |
| zona_mas_frecuente_Zona 10 | 0.151281 |
| viajes_14d | 0.127328 |
| viajes_28d | 0.101157 |

### Interpretación

**dias_desde_ultimo_viaje (+0.732171)**  
Es la variable que más empuja la predicción hacia el abandono. Una mayor
cantidad de días sin utilizar la red aumenta el riesgo estimado, lo que tiene
sentido porque representa una disminución reciente de la actividad.

**zona_mas_frecuente_Zona 13 (+0.234181)**  
Cuando Zona 13 es la zona más frecuente de una persona, el modelo aumenta su
puntaje hacia abandono, manteniendo las demás variables constantes. Esto
describe un patrón presente en los datos simulados y no implica que vivir o
viajar en esa zona cause abandono.

**zona_mas_frecuente_Zona 10 (+0.151281)**  
La presencia de Zona 10 como zona más frecuente también empuja el puntaje
hacia la clase positiva. Al igual que con Zona 13, debe interpretarse como una
asociación encontrada por el modelo y no como una relación causal.

**viajes_14d (+0.127328)**  
Manteniendo constantes las demás variables, una mayor cantidad de viajes en
los últimos 14 días aumenta ligeramente el puntaje de abandono. Aunque puede
parecer contrario a lo esperado, esta variable está relacionada con otras
medidas de actividad como viajes_7d, viajes_28d y recencia. Por esto su
coeficiente representa un efecto condicionado por las demás variables y no
debe interpretarse de forma aislada.

**viajes_28d (+0.101157)**  
También presenta un coeficiente positivo pequeño. Esto no significa que viajar
más cause abandono. Debido a que el modelo incluye varias variables de
frecuencia y recencia al mismo tiempo, el coeficiente refleja la contribución
de viajes_28d después de considerar las demás características relacionadas.

## Conclusión

Los resultados muestran que la recencia es una señal importante del abandono,
pero la regresión logística logra mejorar el desempeño al combinarla con
información de frecuencia, uso de modos, gasto, zonas y comportamiento
temporal.

La mejor regresión logística de esta fase fue L2 con λ = 100 y C = 0.01.

Esta configuración queda como referencia para compararla posteriormente con
el ensemble utilizando exactamente los mismos folds.

El corte B se mantiene sin utilizar para evaluación hasta la fase
correspondiente al test único.