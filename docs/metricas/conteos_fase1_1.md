# Conteos de ingesta - Fase 1.1

| archivo                       | via_ingesta   |   filas_origen |   filas_bronze |   archivos_parquet | estado   |
|:------------------------------|:--------------|---------------:|---------------:|-------------------:|:---------|
| tm_estaciones.csv             | Batch         |            104 |            104 |                  1 | OK       |
| tu_paradas.csv                | Batch         |            328 |            328 |                  1 | OK       |
| mr_estaciones.csv             | Batch         |             22 |             22 |                  1 | OK       |
| am_estaciones.csv             | Batch         |             14 |             14 |                  1 | OK       |
| transmetro_validaciones.csv   | Streaming     |         363221 |         363221 |                  8 | OK       |
| transurbano_transacciones.csv | Streaming     |         832791 |         832791 |                 17 | OK       |
| metroriel_viajes.jsonl        | Batch         |         299100 |         299100 |                  1 | OK       |
| aerometro_boardings.csv       | Streaming     |         203554 |         203554 |                  5 | OK       |
| cdc_padron_usuarios.csv       | CDC           |          31050 |          31050 |                  1 | OK       |
