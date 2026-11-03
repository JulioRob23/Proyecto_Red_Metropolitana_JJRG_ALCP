with completo as (

    select
        unidad_id,
        fecha_corte,
        corte,

        viajes_7d,
        viajes_14d,
        viajes_28d,
        dias_activos_28d,
        dias_desde_ultimo_viaje,
        cantidad_modos_28d,
        es_multimodal,
        modo_mas_usado,
        zona_mas_frecuente,
        proporcion_hora_pico,
        proporcion_dia_habil,
        gasto_total_28d,
        gasto_promedio_28d,
        proporcion_transmetro,
        proporcion_transurbano,
        proporcion_metroriel,
        proporcion_aerometro

    from {{ ref('audit_features_a_completo') }}

),

recortado as (

    select
        unidad_id,
        fecha_corte,
        corte,

        viajes_7d,
        viajes_14d,
        viajes_28d,
        dias_activos_28d,
        dias_desde_ultimo_viaje,
        cantidad_modos_28d,
        es_multimodal,
        modo_mas_usado,
        zona_mas_frecuente,
        proporcion_hora_pico,
        proporcion_dia_habil,
        gasto_total_28d,
        gasto_promedio_28d,
        proporcion_transmetro,
        proporcion_transurbano,
        proporcion_metroriel,
        proporcion_aerometro

    from {{ ref('audit_features_a_recortado') }}

),

solo_completo as (

    select *
    from completo

    except

    select *
    from recortado

),

solo_recortado as (

    select *
    from recortado

    except

    select *
    from completo

),

diferencias as (

    select *
    from solo_completo

    union all

    select *
    from solo_recortado

)

select *
from diferencias