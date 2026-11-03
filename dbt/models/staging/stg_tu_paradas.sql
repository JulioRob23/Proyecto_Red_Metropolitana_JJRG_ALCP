select

    cod_parada,
    descripcion,
    ruta,
    sector,

    _ingested_at::timestamptz as ingested_at,
    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'tu_paradas_raw') }}