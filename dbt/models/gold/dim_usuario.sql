with resumen as (

    select

        usuario_id,

        count(
            distinct sistema
        ) as cantidad_sistemas,

        string_agg(
            distinct sistema,
            ', '
            order by sistema
        ) as sistemas_observados,

        max(
            case
                when metodo_identidad
                    = 'AISLADO_SIN_CROSSWALK'
                then 1
                else 0
            end
        ) = 1
            as identidad_aislada

    from {{ ref('bridge_identidad_usuarios') }}

    group by usuario_id

)

select

    row_number() over (
        order by usuario_id
    )::bigint
        as usuario_key,

    usuario_id,

    cantidad_sistemas,

    sistemas_observados,

    case

        when cantidad_sistemas >= 2
            then true

        else false

    end as es_multimodal_aprox,

    identidad_aislada

from resumen