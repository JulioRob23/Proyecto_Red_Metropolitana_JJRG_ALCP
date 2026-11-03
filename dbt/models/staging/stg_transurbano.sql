select

    to_timestamp(
        fecha || ' ' || hora,
        'DD/MM/YYYY HH24:MI:SS'
    ) as fecha_hora,

    num_tarjeta,
    nullif(cod_parada, '') as cod_parada,
    ruta,

    monto_centavos::integer as monto_centavos,
    cod_estado::integer as cod_estado,

    _row_number::bigint as row_number,
    _ingested_at::timestamptz as ingested_at,

    _source_file as source_file,
    _source_sha256 as source_sha256

from {{ source('raw', 'transurbano_transacciones_raw') }}