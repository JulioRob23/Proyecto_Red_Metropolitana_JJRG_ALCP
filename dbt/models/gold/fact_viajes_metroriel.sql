with viajes as (

    select

        m.trip_id,
        m.usuario_id,

        m.entry_station,
        m.fecha_hora_entrada_local,
        m.zona_origen,

        m.exit_station,
        m.fecha_hora_salida_local,
        m.zona_destino,

        m.fare_gtq,
        m.duration_s

    from {{ ref('silver_metroriel_viajes') }} m

),

con_dimensiones as (

    select

        v.*,

        u.usuario_key,

        modo.modo_key,

        zona_origen.zona_key
            as zona_origen_key,

        zona_destino.zona_key
            as zona_destino_key,

        punto_origen.punto_servicio_key
            as punto_origen_key,

        punto_destino.punto_servicio_key
            as punto_destino_key,

        to_char(
            date_trunc(
                'minute',
                v.fecha_hora_entrada_local
            ),
            'YYYYMMDDHH24MI'
        )::bigint
            as tiempo_entrada_key,

        to_char(
            date_trunc(
                'minute',
                v.fecha_hora_salida_local
            ),
            'YYYYMMDDHH24MI'
        )::bigint
            as tiempo_salida_key

    from viajes v

    left join {{ ref('dim_usuario') }} u
        on v.usuario_id = u.usuario_id

    left join {{ ref('dim_modo') }} modo
        on modo.modo_codigo = 'METRORIEL'

    left join {{ ref('dim_zona') }} zona_origen
        on v.zona_origen = zona_origen.zona_nombre

    left join {{ ref('dim_zona') }} zona_destino
        on v.zona_destino = zona_destino.zona_nombre

    left join {{ ref('dim_punto_servicio') }} punto_origen
        on punto_origen.modo_codigo = 'METRORIEL'
       and punto_origen.codigo_fuente
            = v.entry_station::text

    left join {{ ref('dim_punto_servicio') }} punto_destino
        on punto_destino.modo_codigo = 'METRORIEL'
       and punto_destino.codigo_fuente
            = v.exit_station::text

)

select

    row_number() over (
        order by trip_id
    )::bigint
        as viaje_key,

    trip_id,

    usuario_key,
    modo_key,

    tiempo_entrada_key,
    tiempo_salida_key,

    zona_origen_key,
    zona_destino_key,

    punto_origen_key,
    punto_destino_key,

    1::integer
        as cantidad_viajes,

    fare_gtq
        as tarifa_gtq,

    duration_s
        as duracion_segundos

from con_dimensiones