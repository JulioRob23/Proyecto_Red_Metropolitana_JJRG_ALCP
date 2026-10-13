# Inventario de la capa Gold

## Modelo dimensional

| Relación | Tipo | Filas |
|---|---|---:|
| `dim_modo` | Tabla | 4 |
| `dim_punto_servicio` | Tabla | 468 |
| `dim_tiempo` | Tabla | 64,800 |
| `dim_usuario` | Tabla | 70,380 |
| `dim_zona` | Tabla | 16 |
| `fact_abordajes` | Tabla | 1,688,959 |
| `fact_viajes_metroriel` | Tabla | 295,511 |

## Vistas analíticas

- `vw_abordajes_analitica`
- `vw_cobertura_zonas`
- `vw_metroriel_demanda`
- `vw_usuarios_multimodales`

Las vistas analíticas se construyeron en la Fase 2 para facilitar el consumo
de Gold desde Tableau. No sustituyen al modelo dimensional principal.

## Total de relaciones en Gold

- 7 tablas.
- 4 vistas.
- 11 relaciones en total.