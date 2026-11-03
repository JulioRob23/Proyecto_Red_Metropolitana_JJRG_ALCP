{{ config(materialized='view') }}

-- ============================================================
-- EVENTOS VÁLIDOS UNIFICADOS - PROYECTO 2
-- Una fila representa un abordaje/viaje válido.
-- La fuente siempre es Silver, por lo que Quarantine queda fuera.
-- ============================================================

with transmetro as (

    select
        usuario_id,
        fecha_hora_local as fecha_hora,
        'TRANSMETRO'::text as modo

    from {{ ref('silver_transmetro_validaciones') }}

    where usuario_id is not null
      and fecha_hora_local is not null

),

transurbano as (

    select
        usuario_id,

        -- La columna es timestamptz.
        -- La convertimos explícitamente a hora local de Guatemala
        -- para que todos los operadores usen el mismo reloj.
        (
            fecha_hora_local
            at time zone 'America/Guatemala'
        ) as fecha_hora,

        'TRANSURBANO'::text as modo

    from {{ ref('silver_transurbano_transacciones') }}

    where usuario_id is not null
      and fecha_hora_local is not null

),

metroriel as (

    select
        usuario_id,
        fecha_hora_entrada_local as fecha_hora,
        'METRORIEL'::text as modo

    from {{ ref('silver_metroriel_viajes') }}

    where usuario_id is not null
      and fecha_hora_entrada_local is not null

),

aerometro as (

    select
        usuario_id,
        fecha_hora_local as fecha_hora,
        'AEROMETRO'::text as modo

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