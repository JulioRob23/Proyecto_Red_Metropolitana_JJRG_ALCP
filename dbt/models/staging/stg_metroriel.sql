with source_data as (

    select

        _line_number::bigint as line_number,

        raw_json::jsonb as registro,

        _ingested_at::timestamptz as ingested_at,
        _source_file as source_file,
        _source_sha256 as source_sha256

    from {{ source('raw', 'metroriel_viajes_raw') }}

)

select

    (registro ->> 'trip_id')::bigint as trip_id,

    registro ->> 'card' as card,

    (registro -> 'entry' ->> 'station')::integer
        as entry_station,

    (registro -> 'entry' ->> 'ts')::timestamp
        as entry_ts,

    case
        when registro -> 'exit' is null
          or registro -> 'exit' = 'null'::jsonb
        then null
        else (registro -> 'exit' ->> 'station')::integer
    end as exit_station,

    case
        when registro -> 'exit' is null
          or registro -> 'exit' = 'null'::jsonb
        then null
        else (registro -> 'exit' ->> 'ts')::timestamp
    end as exit_ts,

    (registro ->> 'fare_gtq')::numeric(10,2)
        as fare_gtq,

    (registro ->> 'duration_s')::integer
        as duration_s,

    line_number,
    ingested_at,
    source_file,
    source_sha256

from source_data