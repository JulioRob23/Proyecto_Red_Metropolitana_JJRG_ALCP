select

    validacion_id::bigint as validacion_id,
    tarjeta,
    estacion_id,
    linea,

    fecha_hora::timestamp as fecha_hora,

    tarifa::numeric(10,2) as tarifa_gtq,

    tipo,

    _row_number::bigint as row_number,
    _ingested_at::timestamptz as ingested_at,

    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'transmetro_validaciones_raw') }}