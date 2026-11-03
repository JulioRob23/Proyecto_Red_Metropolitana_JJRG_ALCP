# Fase 1.2 - Etiqueta, población y unidad

## Unidad elegida

Para este proyecto utilizamos la persona como unidad de análisis, representada
mediante `usuario_id`. Esta decisión mantiene la estrategia de identidad que
construimos en el Proyecto 1, donde las llaves de Transmetro, Transurbano y
MetroRiel se relacionan cuando comparten el núcleo numérico utilizado para la
integración.

Trabajar a nivel de persona permite evitar que un usuario que cambia de tarjeta
u operador sea considerado automáticamente como un abandono de la red. Cuando
no existe información suficiente para relacionar una identidad, preferimos
mantenerla separada antes que crear una relación que no podamos justificar.

Aerómetro es la principal limitación de esta estrategia, ya que su `user_hash`
no tiene un crosswalk confiable con los demás operadores.

## Definición de la población

Una persona entra en la población de un corte cuando registra al menos dos
abordajes válidos durante los 28 días anteriores a la fecha de corte y no tiene
un evento DELETE del CDC aplicado antes de dicha fecha.

Solo utilizamos registros provenientes de Silver, por lo que los registros
identificados como inválidos y enviados a cuarentena no forman parte del
cálculo.

## Definición de la etiqueta

La etiqueta vale 1 cuando una persona de la población no registra ningún
abordaje válido en ningún operador durante los 30 días que comienzan en la
fecha de corte, y vale 0 cuando registra al menos uno.

## Resultados

| Corte | Fecha de corte | Población | Positivos | Tasa positiva | Cuenta completa |
|---|---|---:|---:|---:|---|
| A | 2026-07-01 | 59,999 | 8,310 | 0.1385 | 8,310 / 59,999 = 0.1385 |
| B | 2026-07-31 | 54,279 | 15,125 | 0.2787 | 15,125 / 54,279 = 0.2787 |

En el corte A, el 13.85% de las personas de la población dejó de registrar
actividad durante los 30 días siguientes. En el corte B, esta proporción fue
27.87%.

## Costo de la unidad elegida

La tabla de identidad contiene 145,561 llaves fuente. De ellas, 16,930 no
pudieron enlazarse con identidades de otros operadores, equivalente a:

16,930 / 145,561 = 0.1163

Por lo tanto, el 11.63% de las llaves fuente permanece sin enlace.

Las 16,930 llaves no enlazadas corresponden a Aerómetro. Para este operador se
conservó cada `user_hash` como una identidad independiente mediante el método
`AISLADO_SIN_CROSSWALK`, ya que no existe una llave confiable que permita
relacionarla con Transmetro, Transurbano o MetroRiel.

Esta decisión evita crear relaciones falsas, aunque tiene como costo que una
persona que utilice Aerómetro y otro operador puede aparecer como dos personas
distintas.

## Validación técnica

Los modelos `int_eventos_validos_p2` y `poblacion_etiquetas_p2` se construyeron
correctamente mediante dbt.

La prueba `assert_poblacion_etiquetas_p2` valida que:

- no existan duplicados por unidad y fecha de corte;
- todas las unidades tengan al menos dos abordajes previos;
- ninguna unidad incluida tenga un DELETE previo al corte;
- la etiqueta solo contenga los valores 0 y 1.

La prueba terminó con estado PASS.