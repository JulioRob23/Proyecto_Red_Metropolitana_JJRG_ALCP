select

    m.trip_id,
    m.card,
    i.usuario_id,

    m.entry_station,
    entrada.nombre_estacion
        as estacion_origen_nombre,

    {{ normalizar_zona('entrada.zona_nombre') }}
        as zona_origen,

    m.entry_ts
        as fecha_hora_entrada_local,

    m.exit_station,
    salida.nombre_estacion
        as estacion_destino_nombre,

    {{ normalizar_zona('salida.zona_nombre') }}
        as zona_destino,

    m.exit_ts
        as fecha_hora_salida_local,

    m.fare_gtq,
    m.duration_s,

    m.line_number,
    m.ingested_at,
    m.source_file,
    m.source_sha256

from {{ ref('stg_metroriel') }} m

left join {{ ref('stg_mr_estaciones') }} entrada
    on m.entry_station = entrada.id_estacion

left join {{ ref('stg_mr_estaciones') }} salida
    on m.exit_station = salida.id_estacion
left join {{ ref('bridge_identidad_usuarios') }} i
    on i.sistema = 'METRORIEL'
    and i.clave_fuente = m.card
where m.exit_station is not null
  and m.exit_ts is not null