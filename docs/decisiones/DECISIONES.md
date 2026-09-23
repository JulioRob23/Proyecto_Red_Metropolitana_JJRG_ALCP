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