with zonas as (

    -- Transmetro
    select
        {{ normalizar_zona('zona') }}
            as zona_nombre
    from {{ ref('stg_tm_estaciones') }}

    union

    -- Transurbano
    select
        {{ normalizar_zona('sector') }}
            as zona_nombre
    from {{ ref('stg_tu_paradas') }}

    union

    -- MetroRiel
    select
        {{ normalizar_zona('zona_nombre') }}
            as zona_nombre
    from {{ ref('stg_mr_estaciones') }}

    union

    -- Aerómetro
    select
        {{ normalizar_zona('district') }}
            as zona_nombre
    from {{ ref('stg_am_estaciones') }}

    union

    -- Zonas de residencia observadas en el padrón
    -- de Transmetro. Esto permite conservar también
    -- zonas que actualmente no tienen servicio.
    select
        {{ normalizar_zona('zona_residencia') }}
            as zona_nombre
    from {{ ref('stg_cdc_padron') }}
    where tarjeta ~ '^TC-[0-9]{8}$'
      and zona_residencia is not null

),

zonas_unicas as (

    select distinct
        zona_nombre

    from zonas

    where zona_nombre is not null

)

select

    row_number()
        over (
            order by zona_nombre
        ) as zona_id,

    zona_nombre

from zonas_unicas