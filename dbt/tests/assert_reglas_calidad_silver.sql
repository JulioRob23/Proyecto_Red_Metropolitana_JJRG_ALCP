select
    'TRANSURBANO_PARADA_NULA' as problema

where exists (

    select 1

    from {{ ref('silver_transurbano_transacciones') }}

    where cod_parada is null

)


union all


select
    'TRANSURBANO_FECHA_FUTURA' as problema

where exists (

    select 1

    from {{ ref('silver_transurbano_transacciones') }}

    where fecha_hora_local
        > timestamp '2026-07-15 23:59:59'

)


union all


select
    'METRORIEL_SIN_SALIDA' as problema

where exists (

    select 1

    from {{ ref('silver_metroriel_viajes') }}

    where exit_station is null
       or fecha_hora_salida_local is null

)