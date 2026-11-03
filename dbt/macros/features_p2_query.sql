{% macro features_p2_query(cortes, fecha_max_datos=none) %}

with cortes as (

    {% for corte in cortes %}

    select
        '{{ corte[0] }}'::text as corte,
        timestamp '{{ corte[1] }} 00:00:00' as fecha_corte

    {% if not loop.last %}
    union all
    {% endif %}

    {% endfor %}

),

eventos_base as (

    select
        usuario_id,
        fecha_hora,
        modo,
        monto_gtq,
        zona_nombre

    from {{ ref('int_eventos_validos_p2') }}

    {% if fecha_max_datos is not none %}

    where fecha_hora <
        timestamp '{{ fecha_max_datos }} 00:00:00'

    {% endif %}

),

eventos_ventana as (

    select
        c.corte,
        c.fecha_corte,
        e.usuario_id,
        e.fecha_hora,
        e.modo,
        e.monto_gtq,
        e.zona_nombre

    from cortes c

    join eventos_base e
        on e.fecha_hora >=
            c.fecha_corte - interval '28 days'

       and e.fecha_hora <
            c.fecha_corte

),

delete_previos as (

    select distinct
        c.corte,
        s.usuario_id

    from cortes c

    join {{ ref('scd2_padron_transmetro') }} s
        on s.valid_from < c.fecha_corte

    where upper(
        coalesce(
            s.operacion,
            ''
        )
    ) = 'DELETE'

      and s.usuario_id is not null

),

poblacion as (

    select
        e.corte,
        e.fecha_corte,
        e.usuario_id

    from eventos_ventana e

    left join delete_previos d
        on e.corte = d.corte
       and e.usuario_id = d.usuario_id

    where d.usuario_id is null

    group by
        e.corte,
        e.fecha_corte,
        e.usuario_id

    having count(*) >= 2

),

eventos_poblacion as (

    select
        e.*

    from eventos_ventana e

    inner join poblacion p
        on e.corte = p.corte
       and e.fecha_corte = p.fecha_corte
       and e.usuario_id = p.usuario_id

),

base as (

    select
        corte,
        fecha_corte,
        usuario_id,

        count(*) as viajes_28d,

        count(*) filter (
            where fecha_hora >=
                fecha_corte - interval '14 days'
        ) as viajes_14d,

        count(*) filter (
            where fecha_hora >=
                fecha_corte - interval '7 days'
        ) as viajes_7d,

        count(
            distinct fecha_hora::date
        ) as dias_activos_28d,

        count(
            distinct modo
        ) as cantidad_modos_28d,

        extract(
            epoch from (
                fecha_corte
                - max(fecha_hora)
            )
        ) / 86400.0
            as dias_desde_ultimo_viaje,

        sum(
            coalesce(
                monto_gtq,
                0
            )
        ) as gasto_total_28d,

        avg(
            coalesce(
                monto_gtq,
                0
            )
        ) as gasto_promedio_28d,

        avg(
            case
                when extract(
                    isodow from fecha_hora
                ) between 1 and 5
                    then 1.0
                else 0.0
            end
        ) as proporcion_dia_habil,

        avg(
            case
                when extract(
                    hour from fecha_hora
                ) between 6 and 8
                    then 1.0

                when extract(
                    hour from fecha_hora
                ) between 16 and 18
                    then 1.0

                else 0.0
            end
        ) as proporcion_hora_pico,

        (
            count(*) filter (
                where modo = 'TRANSMETRO'
            )
        )::numeric
        / nullif(count(*), 0)
            as proporcion_transmetro,

        (
            count(*) filter (
                where modo = 'TRANSURBANO'
            )
        )::numeric
        / nullif(count(*), 0)
            as proporcion_transurbano,

        (
            count(*) filter (
                where modo = 'METRORIEL'
            )
        )::numeric
        / nullif(count(*), 0)
            as proporcion_metroriel,

        (
            count(*) filter (
                where modo = 'AEROMETRO'
            )
        )::numeric
        / nullif(count(*), 0)
            as proporcion_aerometro

    from eventos_poblacion

    group by
        corte,
        fecha_corte,
        usuario_id

),

modo_ranking as (

    select
        corte,
        fecha_corte,
        usuario_id,
        modo,

        row_number() over (
            partition by
                corte,
                usuario_id

            order by
                count(*) desc,
                modo
        ) as rn

    from eventos_poblacion

    group by
        corte,
        fecha_corte,
        usuario_id,
        modo

),

modo_principal as (

    select
        corte,
        usuario_id,
        modo as modo_mas_usado

    from modo_ranking

    where rn = 1

),

zona_ranking as (

    select
        corte,
        fecha_corte,
        usuario_id,
        zona_nombre,

        row_number() over (
            partition by
                corte,
                usuario_id

            order by
                count(*) desc,
                zona_nombre
        ) as rn

    from eventos_poblacion

    where zona_nombre is not null
      and trim(zona_nombre) <> ''

    group by
        corte,
        fecha_corte,
        usuario_id,
        zona_nombre

),

zona_principal as (

    select
        corte,
        usuario_id,
        zona_nombre
            as zona_mas_frecuente

    from zona_ranking

    where rn = 1

)

select
    b.usuario_id as unidad_id,
    b.fecha_corte,
    b.corte,

    b.viajes_7d,
    b.viajes_14d,
    b.viajes_28d,

    b.dias_activos_28d,

    round(
        b.dias_desde_ultimo_viaje::numeric,
        4
    ) as dias_desde_ultimo_viaje,

    b.cantidad_modos_28d,

    case
        when b.cantidad_modos_28d > 1
            then true
        else false
    end as es_multimodal,

    m.modo_mas_usado,

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
        b.gasto_total_28d::numeric,
        2
    ) as gasto_total_28d,

    round(
        b.gasto_promedio_28d::numeric,
        2
    ) as gasto_promedio_28d,

    round(
        b.proporcion_transmetro::numeric,
        4
    ) as proporcion_transmetro,

    round(
        b.proporcion_transurbano::numeric,
        4
    ) as proporcion_transurbano,

    round(
        b.proporcion_metroriel::numeric,
        4
    ) as proporcion_metroriel,

    round(
        b.proporcion_aerometro::numeric,
        4
    ) as proporcion_aerometro,

    l.etiqueta

from base b

left join modo_principal m
    on b.corte = m.corte
   and b.usuario_id = m.usuario_id

left join zona_principal z
    on b.corte = z.corte
   and b.usuario_id = z.usuario_id

left join {{ ref('poblacion_etiquetas_p2') }} l
    on b.usuario_id = l.unidad_id
   and b.fecha_corte = l.fecha_corte

{% endmacro %}