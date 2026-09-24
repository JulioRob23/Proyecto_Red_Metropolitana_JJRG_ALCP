with esperado as (

    select
        count(*) as cantidad

    from {{ ref('silver_metroriel_viajes') }}

),

real as (

    select
        count(*) as cantidad

    from {{ ref('fact_viajes_metroriel') }}

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