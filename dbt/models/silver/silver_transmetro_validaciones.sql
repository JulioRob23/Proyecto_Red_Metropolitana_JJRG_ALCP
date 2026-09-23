with base as (

    select

        t.*,

        row_number() over (
            partition by validacion_id
            order by row_number
        ) as rn

    from {{ ref('stg_transmetro') }} t

),

validos as (

    select *
    from base
    where rn = 1

)

select

    v.validacion_id,
    v.tarjeta,
    i.usuario_id,
    v.estacion_id,
    v.linea,

    v.fecha_hora
        as fecha_hora_local,

    v.tarifa_gtq,

    v.tipo,

    {{ normalizar_zona('e.zona') }}
        as zona_nombre,

    e.nombre
        as estacion_nombre,

    e.lat,
    e.lon,

    v.row_number,
    v.ingested_at,
    v.source_file,
    v.source_sha256

from validos v

left join {{ ref('stg_tm_estaciones') }} e
    on v.estacion_id = e.estacion_id
left join {{ ref('bridge_identidad_usuarios') }} i
    on i.sistema = 'TRANSMETRO'
    and i.clave_fuente = v.tarjeta