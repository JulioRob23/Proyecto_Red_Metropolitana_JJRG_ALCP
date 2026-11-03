{{ config(materialized='view') }}

select
    usuario_id,
    fecha_hora,
    modo,
    monto_gtq,
    zona_nombre

from {{ ref('int_eventos_validos_p2') }}