select

    a.boarding_id,
    a.user_hash,
    i.usuario_id,
    a.station_code,
    a.axis,

    -- Conservamos también UTC por trazabilidad.
    a.timestamp_utc,

    -- Conversión a hora local de Guatemala.
    (
        a.timestamp_utc
        at time zone 'America/Guatemala'
    ) as fecha_hora_local,

    a.cabin_number,
    a.fare_gtq,

    {{ normalizar_zona('e.district') }}
        as zona_nombre,

    e.station_name
        as estacion_nombre,

    a.row_number,
    a.ingested_at,
    a.source_file,
    a.source_sha256

from {{ ref('stg_aerometro') }} a

left join {{ ref('stg_am_estaciones') }} e
    on a.station_code = e.station_code

left join {{ ref('bridge_identidad_usuarios') }} i
    on i.sistema = 'AEROMETRO'
    and i.clave_fuente = a.user_hash