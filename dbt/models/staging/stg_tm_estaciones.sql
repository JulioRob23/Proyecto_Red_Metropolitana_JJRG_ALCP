select

    estacion_id,
    nombre,
    linea,
    zona,

    nullif(lat, '')::numeric as lat,
    nullif(lon, '')::numeric as lon,

    _ingested_at::timestamptz as ingested_at,
    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'tm_estaciones_raw') }}