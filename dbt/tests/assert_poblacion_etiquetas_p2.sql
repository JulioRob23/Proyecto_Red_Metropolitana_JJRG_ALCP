with duplicados as (

    select
        unidad_id,
        fecha_corte,
        count(*) as cantidad

    from {{ ref('poblacion_etiquetas_p2') }}

    group by
        unidad_id,
        fecha_corte

    having count(*) > 1

),

errores as (

    select
        'unidad_fecha_duplicada' as error,
        count(*) as cantidad
    from duplicados

    union all

    select
        'menos_de_2_abordajes_previos' as error,
        count(*) as cantidad
    from {{ ref('poblacion_etiquetas_p2') }}
    where abordajes_previos_28d < 2

    union all

    select
        'delete_previo_presente' as error,
        count(*) as cantidad
    from {{ ref('poblacion_etiquetas_p2') }}
    where tiene_delete_previo = true

    union all

    select
        'etiqueta_invalida' as error,
        count(*) as cantidad
    from {{ ref('poblacion_etiquetas_p2') }}
    where etiqueta not in (0, 1)
       or etiqueta is null

)

select *
from errores
where cantidad <> 0