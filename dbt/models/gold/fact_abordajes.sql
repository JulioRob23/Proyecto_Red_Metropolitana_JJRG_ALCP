with abordajes as (

    -- ==================================================
    -- TRANSMETRO
    -- ==================================================

    select

        'TRANSMETRO'::text
            as modo_codigo,

        validacion_id::text
            as evento_id,

        usuario_id,

        fecha_hora_local,

        estacion_id::text
            as codigo_punto,

        zona_nombre,

        tarifa_gtq
            as monto_gtq

    from {{ ref('silver_transmetro_validaciones') }}


    union all


    -- ==================================================
    -- TRANSURBANO
    -- ==================================================

    select

        'TRANSURBANO'::text,

        transaccion_id::text,

        usuario_id,

        fecha_hora_local,

        cod_parada::text,

        zona_nombre,

        monto_gtq

    from {{ ref('silver_transurbano_transacciones') }}


    union all


    -- ==================================================
    -- METRORIEL
    -- Cada viaje completo aporta un abordaje
    -- correspondiente a la entrada.
    -- ==================================================

    select

        'METRORIEL'::text,

        trip_id::text,

        usuario_id,

        fecha_hora_entrada_local,

        entry_station::text,

        zona_origen,

        fare_gtq

    from {{ ref('silver_metroriel_viajes') }}


    union all


    -- ==================================================
    -- AERÓMETRO
    -- ==================================================

    select

        'AEROMETRO'::text,

        boarding_id::text,

        usuario_id,

        fecha_hora_local,

        station_code::text,

        zona_nombre,

        fare_gtq

    from {{ ref('silver_aerometro_boardings') }}

),

con_dimensiones as (

    select

        a.*,

        u.usuario_key,

        m.modo_key,

        z.zona_key,

        p.punto_servicio_key,

        to_char(
            date_trunc(
                'minute',
                a.fecha_hora_local
            ),
            'YYYYMMDDHH24MI'
        )::bigint
            as tiempo_key

    from abordajes a

    left join {{ ref('dim_usuario') }} u
        on a.usuario_id = u.usuario_id

    left join {{ ref('dim_modo') }} m
        on a.modo_codigo = m.modo_codigo

    left join {{ ref('dim_zona') }} z
        on a.zona_nombre = z.zona_nombre

    left join {{ ref('dim_punto_servicio') }} p
        on a.modo_codigo = p.modo_codigo
       and a.codigo_punto = p.codigo_fuente

)

select

    row_number() over (

        order by
            modo_codigo,
            evento_id

    )::bigint
        as abordaje_key,

    usuario_key,
    modo_key,
    tiempo_key,
    zona_key,
    punto_servicio_key,

    -- Identificador degenerado del evento.
    evento_id,

    1::integer
        as cantidad_abordajes,

    monto_gtq

from con_dimensiones