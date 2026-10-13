# Índice de Decisiones de Diseño

## Objetivo

Este documento consolida las principales decisiones técnicas tomadas durante
el desarrollo del proyecto y permite localizar rápidamente su justificación.

---

## 1. Arquitectura por capas

**Decisión:** utilizar Bronze, Staging, Silver y Gold.

**Motivo:** separar la ingesta, el procesamiento temporal, la información
validada y el consumo analítico.

**Documentación relacionada:**

- `docs/decisiones/DECISIONES.md`
- `docs/decisiones/DISENO_GOLD.md`

---

## 2. Bronze acumulativo

**Decisión:** conservar Bronze como histórico acumulativo en archivos
Parquet.

**Motivo:** mantener trazabilidad, permitir reprocesamiento y evitar pérdida
del dato original.

---

## 3. Staging temporal

**Decisión:** utilizar Staging como zona operacional temporal que puede
vaciarse y reconstruirse.

**Motivo:** Staging no constituye el histórico oficial. Esa función la
cumple Bronze.

---

## 4. Cuarentena

**Decisión:** los registros inválidos no se eliminan silenciosamente.

**Motivo:** conservar evidencia, trazabilidad y posibilidad de
reprocesamiento.

Las reglas oficiales se encuentran en:


docs/fase3/gobernanza/REGLAS_CALIDAD.md


---

## 5. Identidad conformada

**Decisión:** construir una identidad seudonimizada aproximada entre
Transmetro, Transurbano y MetroRiel.

Aerómetro conserva identidad aislada.

**Motivo:** no existe una llave maestra común y confiable entre los cuatro
operadores.

**Limitación:** multimodalidad aproximada no equivale a transbordo físico.

---

## 6. Dos tablas de hechos en Gold

**Decisión:** mantener:


fact_abordajes
fact_viajes_metroriel


**Motivo:** un abordaje y un viaje completo de MetroRiel poseen diferente
grano y no deben representar el mismo concepto.

---

## 7. MetroRiel dentro de fact_abordajes

**Decisión:** utilizar la entrada del viaje MetroRiel como evento comparable
con los abordajes de los demás sistemas.

El viaje completo se conserva adicionalmente en:

fact_viajes_metroriel


---

## 8. Tableau consume Gold

**Decisión:** Tableau consume vistas analíticas construidas desde Gold.

**Motivo:** Gold representa la fuente oficial de consumo analítico y evita
reconstruir reglas de negocio dentro de Tableau.

---

## 9. Features consumen Silver

**Decisión:** la tabla model-ready se genera directamente desde Silver.

**Motivo:** el feature engineering necesita detalle temporal por usuario
antes de ciertas agregaciones analíticas.

---

## 10. Ventanas temporales de features

**Decisión:** utilizar ventanas de:

7 días
30 días
período completo


**Motivo:** el conjunto de datos disponible cubre aproximadamente 45 días.
Una ventana de 90 días no tendría soporte real en la información disponible.

---

## 11. Orquestación

**Decisión:** utilizar Prefect para coordinar las principales etapas.

**Motivo:** disponer de un flujo reproducible y registrar el tiempo de
ejecución por componente.

---

## 12. Calidad mediante cuarentena

**Decisión:** separar registros válidos e inválidos antes de construir
Silver analítico.

**Motivo:** impedir que errores conocidos afecten Gold sin destruir
información original.

---

## 13. Definiciones centralizadas

**Decisión:** las métricas oficiales se definen dentro del pipeline y la
documentación de gobernanza.

**Motivo:** evitar que cada consumidor reconstruya una definición diferente.

---

## 14. Versionamiento progresivo

**Decisión:** desarrollar el proyecto mediante commits por bloques.

**Motivo:** conservar trazabilidad real sobre la evolución del proyecto y
evitar una única subida final.

---

## Documentos relacionados

Las decisiones detalladas pueden encontrarse en:


docs/decisiones/
docs/fase2/
docs/fase3/gobernanza/
docs/fase3/reproducibilidad/
