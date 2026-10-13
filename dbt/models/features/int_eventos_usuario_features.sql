{{ config(materialized='view') }}

with transmetro as (

    select
        usuario_id,
        'TRANSMETRO'::text as modo,
        fecha_hora_local as fecha_hora,
        zona_nombre,
        tarifa_gtq as monto_gtq
    from {{ ref('silver_transmetro_validaciones') }}
    where usuario_id is not null
      and fecha_hora_local <= timestamp '2026-07-15 23:59:59'

),

transurbano as (

    select
        usuario_id,
        'TRANSURBANO'::text as modo,
        fecha_hora_local::timestamp as fecha_hora,
        zona_nombre,
        monto_gtq
    from {{ ref('silver_transurbano_transacciones') }}
    where usuario_id is not null
      and fecha_hora_local <= timestamp '2026-07-15 23:59:59'

),

metroriel as (

    select
        usuario_id,
        'METRORIEL'::text as modo,
        fecha_hora_entrada_local as fecha_hora,
        zona_origen as zona_nombre,
        fare_gtq as monto_gtq
    from {{ ref('silver_metroriel_viajes') }}
    where usuario_id is not null
      and fecha_hora_entrada_local <= timestamp '2026-07-15 23:59:59'

),

aerometro as (

    select
        usuario_id,
        'AEROMETRO'::text as modo,
        fecha_hora_local as fecha_hora,
        zona_nombre,
        fare_gtq as monto_gtq
    from {{ ref('silver_aerometro_boardings') }}
    where usuario_id is not null
      and fecha_hora_local <= timestamp '2026-07-15 23:59:59'

)

select * from transmetro

union all

select * from transurbano

union all

select * from metroriel

union all

select * from aerometro