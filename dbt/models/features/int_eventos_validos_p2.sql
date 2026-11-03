{{ config(materialized='view') }}

-- ============================================================
-- EVENTOS VÁLIDOS UNIFICADOS - PROYECTO 2
-- Fuente exclusiva: Silver.
-- Una fila representa un abordaje/viaje válido.
-- ============================================================

with transmetro as (

    select
        usuario_id,
        fecha_hora_local as fecha_hora,
        'TRANSMETRO'::text as modo,
        tarifa_gtq::numeric as monto_gtq,
        zona_nombre

    from {{ ref('silver_transmetro_validaciones') }}

    where usuario_id is not null
      and fecha_hora_local is not null

),

transurbano as (

    select
        usuario_id,

        (
            fecha_hora_local
            at time zone 'America/Guatemala'
        ) as fecha_hora,

        'TRANSURBANO'::text as modo,
        monto_gtq::numeric as monto_gtq,
        zona_nombre

    from {{ ref('silver_transurbano_transacciones') }}

    where usuario_id is not null
      and fecha_hora_local is not null

),

metroriel as (

    select
        usuario_id,
        fecha_hora_entrada_local as fecha_hora,
        'METRORIEL'::text as modo,
        fare_gtq::numeric as monto_gtq,
        zona_origen as zona_nombre

    from {{ ref('silver_metroriel_viajes') }}

    where usuario_id is not null
      and fecha_hora_entrada_local is not null

),

aerometro as (

    select
        usuario_id,
        fecha_hora_local as fecha_hora,
        'AEROMETRO'::text as modo,
        fare_gtq::numeric as monto_gtq,
        zona_nombre

    from {{ ref('silver_aerometro_boardings') }}

    where usuario_id is not null
      and fecha_hora_local is not null

)

select * from transmetro

union all

select * from transurbano

union all

select * from metroriel

union all

select * from aerometro