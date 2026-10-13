# Seguridad y Manejo de Datos Personales

## Contexto

Aunque los datos utilizados en el proyecto son generados, la solución se
diseñó considerando el escenario real de una red de transporte, donde los
registros permiten conocer cuándo y dónde utiliza el servicio una persona.

Por esta razón se definen las siguientes medidas de seguridad.

## 1. Manejo de credenciales

Las credenciales no deben almacenarse directamente en el repositorio.

La configuración sensible debe manejarse mediante variables de entorno y
archivos locales excluidos mediante `.gitignore`.

Cuando sea necesario compartir la estructura de configuración se utilizarán
archivos de ejemplo sin valores reales.

El workbook de Tableau tampoco debe almacenar contraseñas de conexión.

**Justificación:** evita que una persona con acceso al repositorio obtenga
automáticamente acceso a PostgreSQL u otros servicios.

## 2. Seudonimización

Los identificadores operacionales originales, como tarjetas o hashes de cada
operador, se utilizan únicamente en las capas necesarias para integración.

Antes del consumo analítico se utiliza `usuario_id`, una identidad
seudonimizada y conformada.

Gold, Features y Tableau no necesitan conocer el número original de tarjeta
para analizar el comportamiento de movilidad.

La seudonimización reduce exposición, aunque no convierte automáticamente los
datos en información anónima debido a que todavía existen patrones de tiempo
y ubicación.

## 3. Acceso según rol

Se aplica el principio de mínimo acceso necesario.

| Rol | Acceso requerido |
|---|---|
| Analista BI | Gold y Tableau |
| Científico de datos | Silver seudonimizado y Features |
| Ingeniero de datos | Bronze, Staging, Silver, Gold y Features |
| Auditor autorizado | Detalle individual únicamente cuando exista una necesidad justificada |
| Usuario ejecutivo | Dashboards y resultados agregados |

Un analista que solamente necesita métricas agregadas no debe acceder al
detalle individual de movilidad.

## 4. Retención

Se propone conservar los datos detallados a nivel individual durante un
máximo de **12 meses**.

Este período permite disponer de un ciclo anual para análisis, auditoría y
comparaciones estacionales sin conservar indefinidamente información de
movilidad individual.

Al finalizar el período de retención, el detalle deberá eliminarse o
anonimizarse, manteniendo únicamente información agregada cuando sea
necesaria para análisis histórico.

Las excepciones deberán estar justificadas y autorizadas por el responsable
de Seguridad de Información y Gobierno de Datos.

## Principio general

La plataforma debe conservar únicamente la información necesaria, durante el
tiempo necesario y accesible únicamente para quienes requieren utilizarla.