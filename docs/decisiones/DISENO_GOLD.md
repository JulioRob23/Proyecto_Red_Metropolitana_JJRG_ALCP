# Diseño dimensional de la capa Gold

## 1. Grano de las tablas de hechos

### fact_abordajes

Una fila representa un abordaje válido realizado por un usuario,
en un modo de transporte, un punto de servicio y un instante determinado.

Para Transmetro, Transurbano y Aerómetro cada registro válido representa
directamente un abordaje.

Para MetroRiel, cada viaje completo genera un abordaje correspondiente
a su evento de entrada. La información completa del trayecto se conserva
por separado en fact_viajes_metroriel.

Esta decisión permite comparar la demanda de los cuatro modos sin inferir
destinos que no existen en las fuentes de Transmetro, Transurbano y Aerómetro.

---

### fact_viajes_metroriel

Una fila representa un viaje completo válido de MetroRiel realizado por
un usuario entre una estación de origen y una estación de destino.

Esta tabla conserva el detalle adicional entregado por MetroRiel sin
forzar a los otros operadores a un grano que sus datos no permiten construir.

---

## 2. Matriz del bus

| Proceso de negocio | Usuario | Modo | Tiempo | Zona | Punto de servicio |
|---|---|---|---|---|---|
| Abordajes de la red | X | X | X | X | X |
| Viajes completos MetroRiel | X | X | X | X | X |

En fact_viajes_metroriel las dimensiones Tiempo, Zona y Punto de servicio
se utilizan con roles diferentes:

- tiempo de entrada;
- tiempo de salida;
- zona de origen;
- zona de destino;
- estación de origen;
- estación de destino.

---

## 3. Dimensiones conformadas

### dim_usuario

Una fila por usuario conformado.

El identificador utilizado en Gold será el usuario_id seudonimizado generado
en Silver. No se expondrán números de tarjeta ni hashes originales de los
operadores.

Atributos principales:

- usuario_key
- usuario_id
- cantidad_sistemas
- es_multimodal_aprox

---

### dim_modo

Contiene los cuatro modos de transporte:

- Transmetro
- Transurbano
- MetroRiel
- Aerómetro

---

### dim_zona

Utiliza la dimensión de zonas conformadas construida en Silver.

Todas las variantes como Z10 y Zona 10 quedan representadas por una sola zona.

---

### dim_tiempo

La dimensión tendrá grano de un minuto y permitirá analizar los eventos
por fecha y hora.

Atributos principales:

- tiempo_key
- fecha
- hora
- minuto
- dia_semana
- es_dia_habil
- es_hora_pico

Para este proyecto se considera día hábil de lunes a viernes.

Se considera hora pico:

- 06:00 a 08:59
- 16:00 a 18:59

Esta definición se documenta como una regla de negocio del proyecto.

---

### dim_punto_servicio

Integra estaciones, paradas y torres de los cuatro operadores.

Atributos principales:

- punto_servicio_key
- modo
- codigo_fuente
- nombre
- linea_ruta_eje
- zona_key
- latitud
- longitud

No todos los operadores entregan coordenadas, por lo que esos campos pueden
ser nulos cuando la fuente no proporciona esa información.

---

## 4. Tablas de hechos

### fact_abordajes

Dimensiones:

- usuario_key
- modo_key
- tiempo_key
- zona_key
- punto_servicio_key

Medidas:

- cantidad_abordajes = 1
- monto_gtq

---

### fact_viajes_metroriel

Dimensiones:

- usuario_key
- modo_key
- tiempo_entrada_key
- tiempo_salida_key
- zona_origen_key
- zona_destino_key
- punto_origen_key
- punto_destino_key

Medidas:

- cantidad_viajes = 1
- tarifa_gtq
- duracion_segundos

---

## 5. Clasificación de medidas

### Medidas aditivas

- cantidad_abordajes
- cantidad_viajes
- monto_gtq
- tarifa_gtq
- duracion_segundos

Se pueden sumar entre registros para obtener totales.

### Medidas semi-aditivas

Las tablas de hechos transaccionales propuestas no contienen una medida base
semi-aditiva.

Una métrica como usuarios activos en una fotografía diaria sería semi-aditiva:
podría agregarse entre zonas o modos, pero no sumarse entre fechas porque el
mismo usuario podría aparecer en varios días.

### Medidas no aditivas

- usuarios_distintos
- tarifa_promedio
- duracion_promedio

Estas métricas deben calcularse nuevamente para cada nivel de agregación y
no deben sumarse entre grupos.

---

## 6. Regla arquitectónica

Todos los modelos Gold se construirán exclusivamente desde la capa Silver.

Gold nunca leerá directamente desde Bronze.