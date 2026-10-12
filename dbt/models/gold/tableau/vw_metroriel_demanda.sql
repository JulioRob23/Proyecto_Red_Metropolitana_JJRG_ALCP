with demanda as (

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

),

ranking as (

    select

        z.zona_key,
        z.zona_nombre,

        coalesce(
            d.abordajes_totales,
            0
        ) as abordajes_totales,

        coalesce(
            d.usuarios_distintos,
            0
        ) as usuarios_distintos,

        case

            when z.zona_nombre in (
                'Zona 12',
                'Zona 8',
                'Zona 1',
                'Zona 6',
                'Zona 17'
            )
                then true

            else false

        end as pertenece_corredor_metroriel

    from {{ ref('dim_zona') }} z

    left join demanda d
        on z.zona_key = d.zona_key

)

select

    zona_key,
    zona_nombre,
    abordajes_totales,
    usuarios_distintos,
    pertenece_corredor_metroriel,

    dense_rank() over (
        order by abordajes_totales desc
    ) as ranking_demanda,

    round(
        (
            abordajes_totales::numeric
            /
            nullif(
                sum(
                    abordajes_totales
                ) over (),
                0
            )
        ) * 100,
        4
    ) as porcentaje_demanda_total

from ranking