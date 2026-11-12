# Fase 2.3 - Segmentación con KMeans y PCA

## Preparación

Se utilizó únicamente la tabla de features del corte A.

Las variables numéricas fueron estandarizadas mediante StandardScaler y las
variables categóricas fueron codificadas mediante One-Hot Encoding.

La etiqueta de abandono no fue utilizada para formar los segmentos.

## Elección de k

Se evaluaron valores de k entre 2 y 8 utilizando dos criterios:

- método del codo mediante la inercia;
- silhouette score.

El mayor silhouette se obtuvo con k = 5 y el método del codo mostró una
reducción progresivamente menor de la inercia alrededor de cinco o seis
clusters.

Por esta razón se seleccionaron cinco segmentos.

## PCA

La visualización se realizó mediante PCA con dos componentes:

- PC1: 27.60% de varianza explicada
- PC2: 19.59% de varianza explicada
- Total: 47.19%

La proyección sirve para visualizar los grupos, pero KMeans fue ajustado con
las 34 dimensiones transformadas y no solamente con las dos dimensiones del
PCA.

## Perfiles de los segmentos


### Segmento 1 - Usuarios principalmente MetroRiel

- Tamaño: 9,968 personas
- Proporción de la población: 16.61%
- Tasa de abandono: 13.95%
- Viajes en 7 días: 2
- Viajes en 14 días: 4
- Viajes en 28 días: 9
- Días activos en 28 días: 7
- Días desde el último viaje: 2.65
- Modos utilizados: 2
- Gasto total mediano: Q21.00
- Modo predominante: METRORIEL
- Zona más frecuente: Zona 1
- Prioridad de retención: Media

**Acción propuesta:** Mantener comunicación de continuidad y beneficios relacionados con MetroRiel, especialmente cuando empiece a aumentar el tiempo desde el último viaje.

### Segmento 2 - Usuarios principalmente Transurbano

- Tamaño: 27,207 personas
- Proporción de la población: 45.35%
- Tasa de abandono: 15.27%
- Viajes en 7 días: 2
- Viajes en 14 días: 5
- Viajes en 28 días: 10
- Días activos en 28 días: 7
- Días desde el último viaje: 2.34
- Modos utilizados: 2
- Gasto total mediano: Q11.70
- Modo predominante: TRANSURBANO
- Zona más frecuente: Zona 10
- Prioridad de retención: Alta

**Acción propuesta:** Priorizar campañas de retención con recordatorios y recargas de cortesía, porque es el segmento más grande y presenta la mayor tasa de abandono.

### Segmento 3 - Usuarios intensivos y muy activos

- Tamaño: 4,152 personas
- Proporción de la población: 6.92%
- Tasa de abandono: 1.49%
- Viajes en 7 días: 17
- Viajes en 14 días: 32
- Viajes en 28 días: 61
- Días activos en 28 días: 22
- Días desde el último viaje: 0.43
- Modos utilizados: 2
- Gasto total mediano: Q90.00
- Modo predominante: TRANSURBANO
- Zona más frecuente: Zona 1
- Prioridad de retención: Baja

**Acción propuesta:** No priorizar incentivos costosos de retención. Mantener seguimiento y beneficios de fidelización, ya que presentan una actividad muy alta y una tasa de abandono muy baja.

### Segmento 4 - Usuarios ocasionales de Aerómetro

- Tamaño: 10,111 personas
- Proporción de la población: 16.85%
- Tasa de abandono: 14.43%
- Viajes en 7 días: 1
- Viajes en 14 días: 3
- Viajes en 28 días: 6
- Días activos en 28 días: 5
- Días desde el último viaje: 3.71
- Modos utilizados: 1
- Gasto total mediano: Q21.00
- Modo predominante: AEROMETRO
- Zona más frecuente: Mixco
- Prioridad de retención: Media-Alta

**Acción propuesta:** Enviar campañas de reactivación e incentivos para volver a utilizar la red, considerando que presentan menor frecuencia y más días desde el último viaje.

### Segmento 5 - Usuarios principalmente Transmetro

- Tamaño: 8,561 personas
- Proporción de la población: 14.27%
- Tasa de abandono: 14.52%
- Viajes en 7 días: 2
- Viajes en 14 días: 4
- Viajes en 28 días: 9
- Días activos en 28 días: 7
- Días desde el último viaje: 2.35
- Modos utilizados: 1
- Gasto total mediano: Q8.00
- Modo predominante: TRANSMETRO
- Zona más frecuente: Zona 10
- Prioridad de retención: Media

**Acción propuesta:** Utilizar recordatorios o promociones de continuidad en Transmetro cuando se detecte una reducción reciente en su actividad.


## Interpretación general

El segmento 2 tiene la mayor tasa de abandono (15.27%) y además representa
la mayor parte de la población, por lo que constituye un grupo importante
para las campañas de retención.

El segmento 3 presenta un comportamiento claramente diferente. Sus usuarios
realizan muchos más viajes, tienen más días activos y registran viajes muy
cerca de la fecha de corte. Su tasa de abandono es solamente 1.49%, por lo
que no sería eficiente priorizar incentivos costosos de retención en este
grupo.

Las tasas de abandono por segmento son descriptivas. La pertenencia a un
segmento no demuestra que el segmento sea la causa del abandono.
