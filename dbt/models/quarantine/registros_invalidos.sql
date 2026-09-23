with tm_base as (

    select

        t.*,

        row_number() over (
            partition by validacion_id
            order by row_number
        ) as rn

    from {{ ref('stg_transmetro') }} t

),

quarantine_tm as (

    select

        'TRANSMETRO'::text
            as fuente,

        validacion_id::text
            as registro_id,

        'QC01_TM_DUPLICADO'::text
            as regla_calidad,

        'Validación duplicada con el mismo validacion_id'::text
            as motivo_rechazo,

        to_jsonb(tm_base)
            as registro_original

    from tm_base

    where rn > 1

),

quarantine_tu_parada as (

    select

        'TRANSURBANO'::text
            as fuente,

        (
            source_sha256
            || ':'
            || row_number::text
        ) as registro_id,

        'QC02_TU_PARADA_NULA'::text
            as regla_calidad,

        'El código de parada está vacío o es nulo'::text
            as motivo_rechazo,

        to_jsonb(t)
            as registro_original

    from {{ ref('stg_transurbano') }} t

    where cod_parada is null

),

quarantine_tu_fecha as (

    select

        'TRANSURBANO'::text
            as fuente,

        (
            source_sha256
            || ':'
            || row_number::text
        ) as registro_id,

        'QC03_TU_FECHA_FUTURA'::text
            as regla_calidad,

        'La fecha se encuentra después de la fecha de corte 2026-07-15'::text
            as motivo_rechazo,

        to_jsonb(t)
            as registro_original

    from {{ ref('stg_transurbano') }} t

    where fecha_hora
        > timestamp '2026-07-15 23:59:59'

),

quarantine_mr as (

    select

        'METRORIEL'::text
            as fuente,

        trip_id::text
            as registro_id,

        'QC04_MR_SIN_SALIDA'::text
            as regla_calidad,

        'El viaje no contiene estación o fecha de salida'::text
            as motivo_rechazo,

        to_jsonb(m)
            as registro_original

    from {{ ref('stg_metroriel') }} m

    where exit_station is null
       or exit_ts is null

)

select * from quarantine_tm

union all

select * from quarantine_tu_parada

union all

select * from quarantine_tu_fecha

union all

select * from quarantine_mr