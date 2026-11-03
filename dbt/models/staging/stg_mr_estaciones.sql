select

    id_estacion::integer as id_estacion,
    nombre_estacion,
    zona_nombre,

    nullif(km, '')::numeric as km,

    _ingested_at::timestamptz as ingested_at,
    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'mr_estaciones_raw') }}
