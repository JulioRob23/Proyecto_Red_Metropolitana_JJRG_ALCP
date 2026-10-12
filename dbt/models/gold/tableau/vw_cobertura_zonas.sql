with puntos as (

    select

        p.zona_key,

        count(*) as cantidad_puntos_servicio,

        count(
            distinct p.modo_key
        ) as cantidad_modos,

        string_agg(
            distinct m.modo_nombre,
            ', '
            order by m.modo_nombre
        ) as modos_disponibles

    from {{ ref('dim_punto_servicio') }} p

    join {{ ref('dim_modo') }} m
        on p.modo_key = m.modo_key

    group by p.zona_key

),

demanda as (

    select

        zona_key,

        sum(
            cantidad_abordajes
        ) as abordajes_totales,

        count(
            distinct usuario_key
        ) as usuarios_distintos

    from {{ ref('fact_abordajes') }}

    group by zona_key

)

select

    z.zona_key,
    z.zona_nombre,

    coalesce(
        p.cantidad_puntos_servicio,
        0
    ) as cantidad_puntos_servicio,

    coalesce(
        p.cantidad_modos,
        0
    ) as cantidad_modos,

    coalesce(
        p.modos_disponibles,
        'Sin servicio'
    ) as modos_disponibles,

    case

        when coalesce(
            p.cantidad_modos,
            0
        ) = 0
            then 'Sin servicio'

        when p.cantidad_modos = 1
            then '1 modo'

        when p.cantidad_modos = 2
            then '2 modos'

        else '3 o más modos'

    end as nivel_cobertura,

    case
        when coalesce(
            p.cantidad_modos,
            0
        ) > 0
            then true
        else false
    end as tiene_servicio,

    coalesce(
        d.abordajes_totales,
        0
    ) as abordajes_totales,

    coalesce(
        d.usuarios_distintos,
        0
    ) as usuarios_distintos

from {{ ref('dim_zona') }} z

left join puntos p
    on z.zona_key = p.zona_key

left join demanda d
    on z.zona_key = d.zona_key