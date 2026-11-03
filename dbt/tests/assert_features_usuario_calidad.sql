with errores as (

    select
        'duplicado_unidad_corte' as error,
        count(*) as cantidad

    from (

        select
            unidad_id,
            fecha_corte

        from {{ ref('features_usuario') }}

        group by
            unidad_id,
            fecha_corte

        having count(*) > 1

    ) x

    union all

    select
        'viajes_28d_menor_2',
        count(*)

    from {{ ref('features_usuario') }}

    where viajes_28d < 2

    union all

    select
        'orden_ventanas_invalido',
        count(*)

    from {{ ref('features_usuario') }}

    where viajes_7d > viajes_14d
       or viajes_14d > viajes_28d

    union all

    select
        'recencia_fuera_rango',
        count(*)

    from {{ ref('features_usuario') }}

    where dias_desde_ultimo_viaje < 0
       or dias_desde_ultimo_viaje > 28

    union all

    select
        'proporcion_fuera_rango',
        count(*)

    from {{ ref('features_usuario') }}

    where proporcion_hora_pico
              not between 0 and 1

       or proporcion_dia_habil
              not between 0 and 1

       or proporcion_transmetro
              not between 0 and 1

       or proporcion_transurbano
              not between 0 and 1

       or proporcion_metroriel
              not between 0 and 1

       or proporcion_aerometro
              not between 0 and 1

    union all

    select
        'etiqueta_A_B_nula',
        count(*)

    from {{ ref('features_usuario') }}

    where corte in ('A', 'B')
      and etiqueta is null

    union all

    select
        'etiqueta_C_no_nula',
        count(*)

    from {{ ref('features_usuario') }}

    where corte = 'C'
      and etiqueta is not null

    union all

    select
        'poblacion_A_no_coincide',
        abs(
            (
                select count(*)
                from {{ ref('features_usuario') }}
                where corte = 'A'
            )
            -
            (
                select count(*)
                from {{ ref('poblacion_etiquetas_p2') }}
                where corte = 'A'
            )
        )

    union all

    select
        'poblacion_B_no_coincide',
        abs(
            (
                select count(*)
                from {{ ref('features_usuario') }}
                where corte = 'B'
            )
            -
            (
                select count(*)
                from {{ ref('poblacion_etiquetas_p2') }}
                where corte = 'B'
            )
        )

)

select *

from errores

where cantidad <> 0