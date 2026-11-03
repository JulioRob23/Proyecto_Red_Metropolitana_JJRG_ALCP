{{ config(materialized='table') }}

-- ============================================================
-- POBLACIÓN Y ETIQUETA DE CHURN - PROYECTO 2
--
-- Unidad: persona / usuario_id
--
-- Población:
--   >= 2 abordajes válidos en los 28 días anteriores al corte
--   y sin DELETE del CDC aplicado antes del corte.
--
-- Etiqueta:
--   1 = ningún abordaje válido en ningún operador durante
--       los 30 días que empiezan en el corte.
--   0 = tuvo al menos un abordaje válido.
-- ============================================================

with cortes as (

    select
        'A'::text as corte,
        timestamp '2026-07-01 00:00:00' as fecha_corte

    union all

    select
        'B'::text as corte,
        timestamp '2026-07-31 00:00:00' as fecha_corte

),

actividad as (

    select
        c.corte,
        c.fecha_corte,
        e.usuario_id as unidad_id,

        count(*) filter (
            where
                e.fecha_hora >=
                    c.fecha_corte - interval '28 days'
                and e.fecha_hora <
                    c.fecha_corte
        ) as abordajes_previos_28d,

        count(*) filter (
            where
                e.fecha_hora >=
                    c.fecha_corte
                and e.fecha_hora <
                    c.fecha_corte + interval '30 days'
        ) as abordajes_futuros_30d

    from cortes c

    join {{ ref('int_eventos_validos_p2') }} e
        on e.fecha_hora >=
            c.fecha_corte - interval '28 days'

       and e.fecha_hora <
            c.fecha_corte + interval '30 days'

    group by
        c.corte,
        c.fecha_corte,
        e.usuario_id

),

usuarios_con_delete_previo as (

    select distinct
        c.corte,
        s.usuario_id

    from cortes c

    join {{ ref('scd2_padron_transmetro') }} s
        on upper(
            coalesce(
                s.operacion,
                ''
            )
        ) = 'DELETE'

       and s.valid_from <
            c.fecha_corte

    where s.usuario_id is not null

),

poblacion as (

    select
        a.corte,
        a.fecha_corte,
        a.unidad_id,
        a.abordajes_previos_28d,
        a.abordajes_futuros_30d,

        case
            when d.usuario_id is not null
                then true
            else false
        end as tiene_delete_previo

    from actividad a

    left join usuarios_con_delete_previo d
        on a.corte = d.corte
       and a.unidad_id = d.usuario_id

    where
        a.abordajes_previos_28d >= 2

        and d.usuario_id is null

)

select
    corte,
    fecha_corte,
    unidad_id,

    abordajes_previos_28d,
    abordajes_futuros_30d,

    tiene_delete_previo,

    case
        when abordajes_futuros_30d = 0
            then 1
        else 0
    end::integer as etiqueta

from poblacion