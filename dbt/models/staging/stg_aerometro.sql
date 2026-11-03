select

    boarding_id::bigint as boarding_id,
    user_hash,
    station_code,
    axis,

    timestamp_utc::timestamptz as timestamp_utc,

    cabin_number::integer as cabin_number,
    fare::numeric(10,2) as fare_gtq,

    _row_number::bigint as row_number,
    _ingested_at::timestamptz as ingested_at,

    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'aerometro_boardings_raw') }}