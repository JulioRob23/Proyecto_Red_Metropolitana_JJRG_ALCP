with puntos_tm as (

    select distinct

        'TRANSMETRO'::text
            as modo_codigo,

        estacion_id::text
            as codigo_fuente,

        estacion_nombre
            as nombre,

        linea
            as linea_ruta_eje,

        zona_nombre,

        lat
            as latitud,

        lon
            as longitud

    from {{ ref('silver_transmetro_validaciones') }}

),

puntos_tu as (

    select distinct

        'TRANSURBANO'::text
            as modo_codigo,

        cod_parada::text
            as codigo_fuente,

        parada_nombre
            as nombre,

        ruta
            as linea_ruta_eje,

        zona_nombre,

        null::numeric
            as latitud,

        null::numeric
            as longitud

    from {{ ref('silver_transurbano_transacciones') }}

),

puntos_mr as (

    select distinct

        'METRORIEL'::text
            as modo_codigo,

        entry_station::text
            as codigo_fuente,

        estacion_origen_nombre
            as nombre,

        'MetroRiel'::text
            as linea_ruta_eje,

        zona_origen
            as zona_nombre,

        null::numeric
            as latitud,

        null::numeric
            as longitud

    from {{ ref('silver_metroriel_viajes') }}

    union

    select distinct

        'METRORIEL'::text,

        exit_station::text,

        estacion_destino_nombre,

        'MetroRiel'::text,

        zona_destino,

        null::numeric,

        null::numeric

    from {{ ref('silver_metroriel_viajes') }}

),

puntos_am as (

    select distinct

        'AEROMETRO'::text
            as modo_codigo,

        station_code::text
            as codigo_fuente,

        estacion_nombre
            as nombre,

        axis
            as linea_ruta_eje,

        zona_nombre,

        null::numeric
            as latitud,

        null::numeric
            as longitud

    from {{ ref('silver_aerometro_boardings') }}

),

todos as (

    select * from puntos_tm

    union all

    select * from puntos_tu

    union all

    select * from puntos_mr

    union all

    select * from puntos_am

),

unicos as (

    select distinct

        modo_codigo,
        codigo_fuente,
        nombre,
        linea_ruta_eje,
        zona_nombre,
        latitud,
        longitud

    from todos

)

select

    row_number() over (

        order by
            u.modo_codigo,
            u.codigo_fuente

    )::bigint
        as punto_servicio_key,

    m.modo_key,

    u.modo_codigo,

    u.codigo_fuente,

    u.nombre,

    u.linea_ruta_eje,

    z.zona_key,

    u.zona_nombre,

    u.latitud,

    u.longitud

from unicos u

left join {{ ref('dim_modo') }} m
    on u.modo_codigo
        = m.modo_codigo

left join {{ ref('dim_zona') }} z
    on u.zona_nombre
        = z.zona_nombre