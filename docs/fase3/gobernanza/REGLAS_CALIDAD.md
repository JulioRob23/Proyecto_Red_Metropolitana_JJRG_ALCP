# Política de Calidad de Datos

## Objetivo

La política de calidad define qué registros se consideran inválidos para
consumo analítico y qué acción debe realizarse cuando se detectan.

El principio general del proyecto es:

**Un registro inválido no se elimina silenciosamente.**

Los datos originales permanecen en Bronze y los registros que incumplen
reglas de calidad se conservan en cuarentena para permitir auditoría,
trazabilidad y posible reprocesamiento.

---

# Flujo general

Dato original
→ Bronze
→ Staging
→ validación de calidad

Si es válido:
→ Silver

Si es inválido:
→ Cuarentena

Gold consume únicamente información validada desde Silver.

---

# Reglas implementadas

## QC01_TM_DUPLICADO

**Fuente:** Transmetro.

**Descripción:** identifica validaciones duplicadas según el identificador
operacional definido para la fuente.

**Problema:** el mismo evento no debe contabilizarse más de una vez dentro
del modelo analítico.

**Acción:**

- conservar el dato original en Bronze;
- registrar el caso en cuarentena;
- excluir la copia duplicada de Silver.

**Cantidad detectada:** 1,115 registros.

---

## QC02_TU_PARADA_NULA

**Fuente:** Transurbano.

**Descripción:** identifica transacciones donde `cod_parada` es nulo.

**Problema:** el evento no puede asociarse correctamente a un punto de
servicio ni a su contexto territorial.

**Acción:**

- conservar el dato original en Bronze;
- registrar el caso en cuarentena;
- excluirlo del conjunto Silver utilizado para análisis territorial.

**Cantidad detectada:** 4,189 registros.

---

## QC03_TU_FECHA_FUTURA

**Fuente:** Transurbano.

**Descripción:** identifica eventos cuya fecha se encuentra fuera del límite
válido definido para el período del proyecto.

**Problema:** representa una fecha futura respecto al intervalo esperado y
podría distorsionar análisis temporales.

**Acción:**

- conservar el registro original;
- enviarlo a cuarentena;
- excluirlo de Silver analítico.

**Cantidad detectada:** 817 registros.

---

## QC04_MR_SIN_SALIDA

**Fuente:** MetroRiel.

**Descripción:** identifica viajes que no poseen estación de salida o fecha
de salida válida.

**Problema:** no es posible representar de manera confiable un viaje
completo origen-destino.

**Acción:**

- conservar el dato original en Bronze;
- registrar la anomalía en cuarentena;
- excluirlo de `silver_metroriel_viajes`;
- no incorporarlo a `fact_viajes_metroriel`.

**Cantidad detectada:** 3,589 registros.

---

# Resumen de calidad

| Regla | Fuente | Registros detectados |
|---|---|---:|
| QC01_TM_DUPLICADO | Transmetro | 1,115 |
| QC02_TU_PARADA_NULA | Transurbano | 4,189 |
| QC03_TU_FECHA_FUTURA | Transurbano | 817 |
| QC04_MR_SIN_SALIDA | MetroRiel | 3,589 |
| **Total de registros/reglas registrados en cuarentena** |  | **9,710** |

El total anterior corresponde a los registros almacenados actualmente en
`quarantine.registros_invalidos`.

---

# Principios de tratamiento

## 1. Bronze es inmutable

Los problemas de calidad no se corrigen sobrescribiendo el dato crudo.

## 2. Los registros inválidos no desaparecen

Los casos rechazados permanecen disponibles en cuarentena.

## 3. Silver contiene información aceptada para consumo

Las transformaciones y reglas de calidad se aplican antes de construir las
capas analíticas.

## 4. Gold no consume Bronze directamente

Toda información incluida en Gold debe haber pasado por las reglas y
transformaciones correspondientes de Silver.

## 5. Las reglas son reproducibles

Las condiciones de calidad están implementadas mediante dbt y pueden
ejecutarse nuevamente sobre los datos.

## 6. Los conteos deben medirse

Una regla de calidad debe reportar cuántos registros afecta y no limitarse
a declarar que existe un problema.

---

# Modificación de reglas

Una regla de calidad solo debe modificarse cuando:

1. existe una necesidad documentada;
2. se identifica el dominio afectado;
3. se analiza el impacto sobre Silver y Gold;
4. el responsable correspondiente aprueba la modificación;
5. se actualizan pruebas y documentación;
6. el cambio queda versionado en Git.