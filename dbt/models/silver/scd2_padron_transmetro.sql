with eventos as (

    select *

    from {{ ref('stg_cdc_padron') }}

    where tarjeta ~ '^TC-[0-9]{8}$'

),

atributos as (

    select

        e.*,

        coalesce(

            e.perfil,

            (
                select p.perfil

                from eventos p

                where p.tarjeta = e.tarjeta
                  and p.seq < e.seq
                  and p.perfil is not null

                order by p.seq desc

                limit 1
            )

        ) as perfil_efectivo,

        coalesce(

            e.zona_residencia,

            (
                select p.zona_residencia

                from eventos p

                where p.tarjeta = e.tarjeta
                  and p.seq < e.seq
                  and p.zona_residencia is not null

                order by p.seq desc

                limit 1
            )

        ) as zona_efectiva,

        case

            when e.op = 'DELETE'
                then 'INACTIVA'

            else coalesce(

                e.estado,

                (
                    select p.estado

                    from eventos p

                    where p.tarjeta = e.tarjeta
                      and p.seq < e.seq
                      and p.estado is not null

                    order by p.seq desc

                    limit 1
                ),

                'ACTIVA'
            )

        end as estado_efectivo,

        case
            when e.op = 'DELETE'
                then false
            else true
        end as activo_efectivo

    from eventos e

),

versiones as (

    select

        *,

        lead(commit_ts) over (

            partition by tarjeta

            order by seq

        ) as valid_to,

        lead(seq) over (

            partition by tarjeta

            order by seq

        ) as siguiente_seq

    from atributos

)

select

    i.usuario_id,

    v.tarjeta,

    v.seq
        as version_seq,

    v.op
        as operacion,

    v.perfil_efectivo
        as perfil,

    {{ normalizar_zona('v.zona_efectiva') }}
        as zona_residencia,

    v.estado_efectivo
        as estado,

    v.activo_efectivo
        as activo,

    v.commit_ts
        as valid_from,

    v.valid_to,

    case
        when v.siguiente_seq is null
            then true
        else false
    end as es_actual

from versiones v

left join {{ ref('bridge_identidad_usuarios') }} i
    on i.sistema = 'TRANSMETRO'
   and i.clave_fuente = v.tarjeta