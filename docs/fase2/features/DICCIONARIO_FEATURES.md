# Diccionario de Features - Fase 2.3

## Definición general

La tabla `features.features_usuario` fue construida directamente desde la
capa Silver.

Su grano es:

**1 fila por usuario.**

La fecha de corte utilizada es:

**15 de julio de 2026 a las 23:59:59.**

No se utilizó una ventana de 90 días debido a que el período disponible
abarca aproximadamente 45 días. Por esta razón se utilizaron ventanas de
7 días, 30 días y el período completo observado.

---

| Campo | Descripción |
|---|---|
| `usuario_id` | Identificador seudonimizado del usuario. |
| `fecha_corte` | Fecha hasta la cual se utiliza información para calcular las variables. |
| `eventos_7d` | Cantidad de interacciones del usuario con la red durante los últimos 7 días. |
| `eventos_30d` | Cantidad de interacciones durante los últimos 30 días. |
| `eventos_periodo` | Total de interacciones durante todo el período disponible. |
| `cantidad_modos` | Número de sistemas distintos en los que fue observado el usuario. |
| `es_multimodal_aprox` | Indica si el usuario fue observado en más de un sistema. |
| `modo_mas_usado` | Sistema donde el usuario registró la mayor cantidad de eventos. |
| `dias_desde_ultima_actividad` | Días transcurridos desde la última actividad hasta la fecha de corte. |
| `zona_mas_frecuente` | Zona donde se concentra la mayor cantidad de eventos del usuario. |
| `proporcion_hora_pico` | Proporción de eventos realizados entre 06:00–08:59 y 16:00–18:59. |
| `proporcion_dia_habil` | Proporción de eventos realizados de lunes a viernes. |
| `gasto_acumulado_gtq` | Monto total pagado por el usuario durante el período observado. |
| `gasto_promedio_gtq` | Monto promedio pagado por evento. |
| `primera_actividad` | Primera fecha y hora observada para el usuario. |
| `ultima_actividad` | Última fecha y hora observada para el usuario. |

## Consideraciones

Los eventos se construyen a partir de los cuatro modelos Silver:
Transmetro, Transurbano, MetroRiel y Aerómetro.

Para MetroRiel se utiliza la entrada del viaje como momento de interacción.

La multimodalidad continúa siendo aproximada debido a la estrategia de
identidad utilizada en la Fase 1. Aerómetro no cuenta con un crosswalk
confiable con los demás operadores.