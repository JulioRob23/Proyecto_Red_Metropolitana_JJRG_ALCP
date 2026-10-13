{{ config(materialized='table') }}

with parametros as (

    select
        timestamp '2026-07-15 23:59:59' as fecha_corte

),

eventos as (

    select *
    from {{ ref('int_eventos_usuario_features') }}

),

base as (

    select

        e.usuario_id,

        count(*) as eventos_periodo,

        count(*) filter (
            where e.fecha_hora >
                p.fecha_corte - interval '7 days'
        ) as eventos_7d,

        count(*) filter (
            where e.fecha_hora >
                p.fecha_corte - interval '30 days'
        ) as eventos_30d,

        count(
            distinct e.modo
        ) as cantidad_modos,

        min(e.fecha_hora) as primera_actividad,

        max(e.fecha_hora) as ultima_actividad,

        extract(
            epoch from (
                p.fecha_corte - max(e.fecha_hora)
            )
        ) / 86400.0
            as dias_desde_ultima_actividad,

        sum(
            coalesce(
                e.monto_gtq,
                0
            )
        ) as gasto_acumulado_gtq,

        avg(
            e.monto_gtq
        ) as gasto_promedio_gtq,

        avg(
            case
                when extract(
                    isodow from e.fecha_hora
                ) between 1 and 5
                    then 1.0
                else 0.0
            end
        ) as proporcion_dia_habil,

        avg(
            case
                when extract(
                    hour from e.fecha_hora
                ) between 6 and 8
                    then 1.0

                when extract(
                    hour from e.fecha_hora
                ) between 16 and 18
                    then 1.0

                else 0.0
            end
        ) as proporcion_hora_pico,

        p.fecha_corte

    from eventos e

    cross join parametros p

    group by
        e.usuario_id,
        p.fecha_corte

),

modo_ranking as (

    select

        usuario_id,
        modo,

        count(*) as cantidad_eventos,

        row_number() over (
            partition by usuario_id
            order by
                count(*) desc,
                modo
        ) as rn

    from eventos

    group by
        usuario_id,
        modo

),

modo_principal as (

    select
        usuario_id,
        modo as modo_mas_usado
    from modo_ranking
    where rn = 1

),

zona_ranking as (

    select

        usuario_id,
        zona_nombre,

        count(*) as cantidad_eventos,

        row_number() over (
            partition by usuario_id
            order by
                count(*) desc,
                zona_nombre
        ) as rn

    from eventos

    where zona_nombre is not null

    group by
        usuario_id,
        zona_nombre

),

zona_principal as (

    select
        usuario_id,
        zona_nombre as zona_mas_frecuente
    from zona_ranking
    where rn = 1

)

select

    b.usuario_id,
    b.fecha_corte,

    b.eventos_7d,
    b.eventos_30d,
    b.eventos_periodo,

    b.cantidad_modos,

    case
        when b.cantidad_modos > 1
            then true
        else false
    end as es_multimodal_aprox,

    m.modo_mas_usado,

    round(
        b.dias_desde_ultima_actividad::numeric,
        2
    ) as dias_desde_ultima_actividad,

    z.zona_mas_frecuente,

    round(
        b.proporcion_hora_pico::numeric,
        4
    ) as proporcion_hora_pico,

    round(
        b.proporcion_dia_habil::numeric,
        4
    ) as proporcion_dia_habil,

    round(
        b.gasto_acumulado_gtq::numeric,
        2
    ) as gasto_acumulado_gtq,

    round(
        b.gasto_promedio_gtq::numeric,
        2
    ) as gasto_promedio_gtq,

    b.primera_actividad,
    b.ultima_actividad

from base b

left join modo_principal m
    on b.usuario_id = m.usuario_id

left join zona_principal z
    on b.usuario_id = z.usuario_id