with esperado as (

    select
        (
            (select count(*)
             from {{ ref('silver_transmetro_validaciones') }})

            +

            (select count(*)
             from {{ ref('silver_transurbano_transacciones') }})

            +

            (select count(*)
             from {{ ref('silver_metroriel_viajes') }})

            +

            (select count(*)
             from {{ ref('silver_aerometro_boardings') }})
        ) as cantidad

),

real as (

    select
        count(*) as cantidad

    from {{ ref('fact_abordajes') }}

)

select

    esperado.cantidad
        as esperado,

    real.cantidad
        as real

from esperado
cross join real

where esperado.cantidad
    <> real.cantidad