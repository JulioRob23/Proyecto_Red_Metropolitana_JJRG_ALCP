select

    seq::bigint as seq,
    commit_ts::timestamp as commit_ts,

    upper(op) as op,
    tarjeta,

    nullif(perfil, '') as perfil,
    nullif(zona_residencia, '') as zona_residencia,
    nullif(estado, '') as estado,

    _ingested_at::timestamptz as ingested_at,

    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'cdc_padron_raw') }}