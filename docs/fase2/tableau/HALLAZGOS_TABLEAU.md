# Hallazgos del tablero - Fase 2.1

## 1. Demanda general

Durante el período observado se registraron 1,688,959 abordajes.

Transurbano presentó el mayor volumen con 827,788 abordajes, seguido por
Transmetro con 362,106, MetroRiel con 295,511 y Aerómetro con 203,554.

## 2. Concentración temporal

La demanda presenta dos picos claros alrededor de las 7:00 y las 17:00.

Las franjas definidas como hora pico concentran 839,033 abordajes,
equivalentes al 49.68% del total observado.

## 3. Demanda territorial

Las cinco zonas con mayor cantidad de abordajes fueron:

1. Zona 17
2. Zona 12
3. Zona 8
4. Zona 6
5. Zona 1

## 4. Cobertura

Santa Catarina Pinula es la única zona conformada que no presenta puntos
de servicio de ninguno de los cuatro modos dentro de los datos disponibles.

El valor de cero abordajes en esta zona no debe interpretarse como ausencia
de necesidad de movilidad, ya que al no existir servicio tampoco se pueden
observar validaciones o abordajes.

## 5. Multimodalidad

Se identificaron 36,829 usuarios multimodales aproximados, equivalentes
al 52.33% de las identidades conformadas.

La combinación más frecuente fue Transmetro + Transurbano, con 16,407
usuarios observados.

La multimodalidad es aproximada debido a la estrategia de identidad definida
en la Fase 1. Aerómetro conserva una identidad aislada por no existir un
crosswalk confiable con los demás operadores.

## 6. MetroRiel

Las zonas 17, 12, 8, 6 y 1, que forman parte del corredor propuesto de
MetroRiel, corresponden exactamente a las cinco zonas con mayor demanda
observada.

En conjunto concentran 733,182 abordajes, equivalentes al 43.41% del total
de la red integrada.

Este resultado muestra una fuerte coincidencia entre el trazado propuesto
y las zonas de mayor demanda, aunque por sí solo no permite afirmar que
MetroRiel resuelva completamente las necesidades de movilidad de la red.

## 7. Rendimiento del tablero

Se realizó una prueba de rendimiento en Tableau Desktop utilizando conexión
Live a PostgreSQL.

Durante la muestra, los eventos de mayor duración correspondieron a
consultas SQL (`Executing Query`), con un tiempo máximo observado de
aproximadamente 13.46 segundos.

Este valor corresponde a una muestra de ejecución durante la navegación
entre los dashboards y no representa un promedio general de todas las
consultas.