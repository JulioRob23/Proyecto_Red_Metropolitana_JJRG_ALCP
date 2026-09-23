# Bitácora de decisiones

## D01 - Uso de PostgreSQL

Se utilizará PostgreSQL como base de datos para las capas de staging, Silver y Gold.

**Justificación:** permite trabajar con una arquitectura similar a un entorno real, facilita el uso de SQL y posteriormente permitirá conectar la capa Gold con Tableau.

---

## D02 - Uso de Python 3.11

Se utilizará un entorno virtual con Python 3.11 para mantener aisladas las dependencias del proyecto y evitar conflictos con otras versiones instaladas en el equipo.

---

## D03 - Almacenamiento de la capa Bronze

La capa Bronze se almacenará como archivos Parquet dentro de un lake local, separados por fuente y particionados por fecha de ingesta.

Los datos de negocio se conservarán sin transformaciones. Únicamente se agregarán columnas técnicas como la fecha de ingesta, el archivo de origen y un hash SHA-256 del archivo.

**Justificación:** Parquet permite almacenar de forma eficiente los diferentes formatos recibidos y soporta posteriormente su procesamiento. Además, mantener Bronze separado del warehouse conserva una copia del dato crudo antes de las transformaciones de Silver.

Para evitar duplicados al ejecutar nuevamente el flujo, cada archivo se identificará mediante su hash SHA-256.

---

## D04 - Ingesta de Transurbano mediante streaming

Las transacciones de Transurbano se procesarán mediante streaming utilizando Kafka.

**Justificación:** cada fila representa una transacción individual generada cuando un usuario utiliza el servicio, por lo que en un ambiente real estos registros podrían llegar continuamente.

La principal ventaja es una menor latencia para disponer de los datos. Como consecuencia, la solución requiere una infraestructura de streaming y manejo de eventos más compleja que una carga batch.

---

## D05 - MetroRiel se ingiere mediante Batch

Los viajes de MetroRiel se procesarán mediante una carga Batch.

**Justificación:** cada registro del archivo representa un viaje completo que ya finalizó, por lo que no es necesario tratar cada dato como un evento individual de streaming.

El archivo original utiliza formato JSON Lines y contiene información anidada. En Bronze se conservará cada línea JSON sin aplanarla. La interpretación y transformación de su estructura se realizará posteriormente en Silver.

---

## D06 - Aerómetro conserva UTC en Bronze

Los abordajes de Aerómetro se ingresarán mediante streaming con Kafka.

La fecha y hora se conservarán en UTC dentro de Bronze, tal como vienen en el archivo original.

**Justificación:** Bronze debe mantener el dato recibido sin aplicar transformaciones de negocio. La conversión de UTC a hora local de Guatemala se realizará posteriormente en la capa Silver.

---

## D07 - Conservación del CDC crudo en Bronze

El archivo cdc_padron_usuarios.csv se ingiere a la capa Bronze conservando todas las operaciones y campos tal como fueron recibidos.

En esta etapa no se aplican las operaciones INSERT, UPDATE ni DELETE.

**Justificación:** Bronze conserva el log original del CDC para mantener trazabilidad y permitir reconstruir posteriormente el estado del padrón. La aplicación ordenada de las operaciones se realizará en Staging durante la Fase 1.2.

---

## D08 - Interpretación del padrón CDC de Transmetro

Aunque el archivo CDC contiene diferentes formatos de llave de usuario, para construir el padrón vigente de Transmetro se utilizarán únicamente las llaves con formato TC-########.

Las llaves numéricas, las llaves MR y el valor SIN-TARJETA se conservarán en Staging y serán contabilizadas, pero no se incorporarán al padrón de Transmetro.

**Justificación:** el enunciado define este proceso como el padrón de Transmetro. Incorporar llaves de otros formatos como si fueran tarjetas de Transmetro implicaría asumir una identidad que los datos no demuestran. La ambigüedad se retomará en la estrategia de identidad de la capa Silver.

Para los DELETE, la tarjeta no se eliminará físicamente. Se conservará y se marcará como inactiva. Si un DELETE aparece sin atributos previos conocidos, se conservará la llave como inactiva sin inventar perfil ni zona.

---

## D09 - Catálogos mínimos para operadores sin padrón

Transurbano, MetroRiel y Aerómetro no proporcionan un padrón de usuarios.

Para cada operador se construirá un catálogo mínimo utilizando únicamente las llaves distintas observadas en sus archivos de operación:

- Transurbano: num_tarjeta
- MetroRiel: card
- Aerómetro: user_hash

No se agregarán nombres, perfiles, fechas de alta ni otros atributos.

**Justificación:** estos operadores no entregaron información adicional sobre sus usuarios. Agregar atributos implicaría inventar datos que no existen en las fuentes originales.

---

## D10 - Reglas iniciales de calidad para Silver

Antes de construir Silver se definen las siguientes reglas de calidad:

### QC01 - Duplicados de Transmetro
Una validación repetida con el mismo identificador de evento se considera duplicada. Se conservará una ocurrencia válida y las repeticiones adicionales se enviarán a cuarentena.

### QC02 - Parada nula de Transurbano
Una transacción con cod_parada vacío o nulo se considera inválida para análisis espacial y se enviará a cuarentena.

### QC03 - Fecha futura de Transurbano
Una transacción cuya fecha se encuentre después de la fecha de corte definida para el procesamiento se considera inválida y se enviará a cuarentena.

### QC04 - Viaje sin salida de MetroRiel
Un viaje cuyo objeto o estación de salida no exista se considera incompleto y se enviará a cuarentena.

Los registros rechazados no se eliminarán. Se almacenarán junto con la fuente y el motivo de rechazo.

---

## D11 - Fecha de corte para validación temporal

Para las reglas de calidad de la Fase 1.3 se utilizará como fecha de corte el 15 de julio de 2026.

**Justificación:** el generador entregado simula 45 días de operación iniciando el 1 de junio de 2026. Por lo tanto, los registros posteriores al 15 de julio de 2026 se consideran fechas futuras o inconsistentes para este conjunto de datos.

---

## D12 - Estrategia de identidad entre operadores

No existe una tabla oficial que relacione las llaves de usuario de los cuatro sistemas.

Para Transmetro, Transurbano y MetroRiel se utilizará como aproximación el núcleo numérico de sus identificadores:

- TC-00013132 → 00013132
- 0000013132 → 00013132
- MR0013132 → 00013132

Cuando el núcleo numérico coincide se asumirá que las llaves corresponden al mismo usuario.

Esta relación es una heurística y no una equivalencia demostrada por una tabla maestra, por lo que debe interpretarse como una aproximación.

Aerómetro utiliza un hash que no puede relacionarse de manera confiable con las demás llaves. Sus usuarios permanecerán como identidades independientes.

Como consecuencia, los análisis multimodales podrán identificar relaciones entre Transmetro, Transurbano y MetroRiel, pero podrían subestimar los transbordos que involucren Aerómetro.

El identificador conformado será seudonimizado mediante SHA-256 antes de llegar a Gold.

---

## D13 - Historización del padrón mediante SCD Tipo 2

El historial del padrón de Transmetro se modelará mediante SCD Tipo 2.

Cada INSERT, UPDATE o DELETE genera una versión temporal del estado de la tarjeta.

Cada versión contiene:

- fecha de inicio de vigencia;
- fecha de fin de vigencia;
- indicador de versión actual;
- perfil;
- zona de residencia;
- estado activo o inactivo.

Los DELETE generan una nueva versión inactiva y conservan los últimos atributos conocidos de la tarjeta.

De esta forma es posible consultar cómo se encontraba una tarjeta en una fecha histórica sin perder los cambios posteriores.