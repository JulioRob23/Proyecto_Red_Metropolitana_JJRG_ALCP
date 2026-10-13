# Definiciones Oficiales de Datos y Métricas

## Objetivo

Este documento establece las definiciones oficiales utilizadas por la
Red Metropolitana para evitar interpretaciones diferentes de una misma
métrica entre operadores, analistas o consumidores de información.

Las definiciones se basan en el modelo integrado construido durante las
Fases 1 y 2.

---

## 1. Abordaje

Un **abordaje** es un evento válido que representa la utilización o ingreso
de un usuario a uno de los modos de transporte integrados.

En Gold se representa mediante una fila de:

`gold.fact_abordajes`

y cada fila válida posee:

`cantidad_abordajes = 1`

Para MetroRiel, la entrada del viaje se utiliza como abordaje para permitir
comparaciones de demanda con los demás modos.

Un abordaje no debe interpretarse necesariamente como un viaje completo.

---

## 2. Viaje MetroRiel

Un **viaje MetroRiel** representa un recorrido completo entre una estación
de entrada y una estación de salida.

Se almacena en:

`gold.fact_viajes_metroriel`

Cada fila representa un viaje válido y contiene información de origen,
destino, tiempos de entrada y salida, tarifa y duración.

Los viajes sin salida válida no se incorporan a este hecho y permanecen
documentados mediante la política de calidad y cuarentena.

---

## 3. Demanda

La **demanda observada** se mide mediante la suma de abordajes válidos:

`SUM(cantidad_abordajes)`

sobre:

`gold.fact_abordajes`

La demanda representa utilización observada de los servicios incluidos en
el proyecto.

La ausencia de abordajes no demuestra necesariamente ausencia de necesidad
de movilidad cuando no existe cobertura disponible.

---

## 4. Usuario

Un **usuario** corresponde a una identidad seudonimizada y conformada
utilizada para relacionar actividad dentro de la red sin exponer
directamente el identificador original de tarjeta.

La representación oficial en Gold es:

`dim_usuario.usuario_id`

---

## 5. Usuario activo

Un **usuario activo** es una identidad conformada que registra al menos un
evento válido dentro del período de análisis seleccionado.

La condición general es:

`COUNT(eventos_validos) >= 1`

dentro del intervalo evaluado.

Por lo tanto, el número de usuarios activos depende explícitamente del
período utilizado y siempre debe reportarse junto con dicho período.

---

## 6. Usuario multimodal aproximado

Un **usuario multimodal aproximado** es una identidad conformada observada
en más de un sistema de transporte enlazable.

En Gold corresponde a:

`es_multimodal_aprox = true`

La condición utilizada es:

`cantidad_sistemas > 1`

Esta métrica no demuestra que haya ocurrido un transbordo físico entre
modos. Únicamente demuestra que la identidad fue observada utilizando más
de un sistema durante el período analizado.

Aerómetro mantiene identidades aisladas debido a que no existe un crosswalk
confiable con los identificadores de los demás operadores.

---

## 7. Identidad aislada

Una **identidad aislada** es un usuario cuyo identificador puede utilizarse
de manera consistente dentro de su propio operador, pero no puede
relacionarse de manera confiable con los demás sistemas.

Esta clasificación se utiliza principalmente para Aerómetro.

---

## 8. Modo de transporte

Un **modo** representa uno de los cuatro sistemas integrados:

- Transmetro
- Transurbano
- MetroRiel
- Aerómetro

La representación oficial se encuentra en:

`gold.dim_modo`

---

## 9. Zona conformada

Una **zona conformada** es una representación territorial estandarizada que
permite analizar conjuntamente registros provenientes de distintos
operadores.

La representación oficial se encuentra en:

`gold.dim_zona`

Los nombres y equivalencias territoriales se normalizan antes de ser
consumidos por Gold.

---

## 10. Punto de servicio

Un **punto de servicio** representa una estación, parada o ubicación física
donde un modo de transporte presta servicio.

La representación oficial se encuentra en:

`gold.dim_punto_servicio`

El concepto unifica:

- estaciones de Transmetro;
- paradas de Transurbano;
- estaciones de MetroRiel;
- estaciones de Aerómetro.

---

## 11. Zona con servicio

Una **zona con servicio** es aquella donde existe al menos un punto de
servicio perteneciente a cualquiera de los cuatro modos integrados.

Formalmente:

`cantidad_modos > 0`

o equivalentemente:

`tiene_servicio = true`

en:

`gold.vw_cobertura_zonas`

---

## 12. Zona sin servicio observado

Una **zona sin servicio observado** es aquella donde el modelo no registra
puntos de servicio de ninguno de los cuatro modos integrados.

Formalmente:

`cantidad_modos = 0`

Esta condición no significa que la zona no posea necesidad de movilidad.
Indica únicamente que no existe cobertura representada dentro de los datos
integrados.

---

## 13. Hora pico

Se consideran **horas pico** las siguientes franjas:

- 06:00 a 08:59
- 16:00 a 18:59

La regla se encuentra materializada en:

`dim_tiempo.es_hora_pico`

La definición se utiliza de manera uniforme en Gold, Tableau y features.

---

## 14. Día hábil

Se considera **día hábil** cualquier fecha comprendida entre lunes y viernes.

La definición se encuentra en:

`dim_tiempo.es_dia_habil`

Esta variable no incorpora feriados oficiales; representa únicamente una
clasificación por día de semana.

---

## 15. Cobertura modal

La **cobertura modal** representa la cantidad de modos de transporte con
presencia de al menos un punto de servicio dentro de una zona.

Se calcula como:

`COUNT(DISTINCT modo)`

por zona.

No debe interpretarse como una medición de frecuencia, capacidad o calidad
del servicio.

---

## 16. Monto en GTQ

Los montos monetarios analíticos se expresan en quetzales.

Cuando una fuente utiliza otra unidad de representación, la conversión se
realiza antes del consumo analítico.

En particular, Transurbano proporciona `monto_centavos`, que se convierte
a `monto_gtq` durante Silver.

---

# Reglas de interpretación

Las métricas deben calcularse utilizando las tablas o vistas oficiales de
Gold.

No deben redefinirse reglas de negocio directamente dentro de Tableau,
hojas de cálculo u otras herramientas de consumo.

Toda modificación de una definición oficial debe quedar documentada,
versionada y autorizada por el dueño del dominio correspondiente.