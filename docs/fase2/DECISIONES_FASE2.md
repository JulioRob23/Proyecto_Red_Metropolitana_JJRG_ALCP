# Decisiones - Fase 2

## D2.1 - Fuentes de consumo por producto

La Fase 2 tendrá dos consumidores principales:

1. Tableau utilizará exclusivamente la capa Gold.
2. La tabla de features para ciencia de datos se construirá desde Silver.

### Justificación

Gold contiene el modelo dimensional preparado para análisis de negocio,
por lo que es la capa adecuada para el tablero.

Silver conserva el detalle atómico de los eventos, necesario para construir
features por usuario y por ventanas temporales sin depender de agregaciones
predefinidas en Gold.

## D2.2 - Reutilización de la Fase 1

La Fase 2 no volverá a limpiar ni reconstruir los datos desde los archivos
Raw o Bronze.

Los análisis utilizarán los datos ya validados en Silver y Gold, manteniendo
el linaje y las reglas de calidad definidas durante la Fase 1.

## D2.3 - Criterio de recomendación de movilidad

La recomendación de la Fase 2 no evalúa a MetroRiel de forma aislada.

Se considera al corredor como parte de una red integrada debido a que los
datos muestran una alta utilización de los modos existentes y evidencia
de multimodalidad aproximada entre los usuarios.

La recomendación se basa principalmente en:

- concentración de demanda por zona;
- cobertura territorial;
- multimodalidad observada;
- coincidencia entre las zonas de mayor demanda y el corredor MetroRiel;
- demanda que permanece fuera del corredor.

Por lo tanto, se propone a MetroRiel como corredor estructurante y no como
sustituto de Transmetro, Transurbano o Aerómetro.