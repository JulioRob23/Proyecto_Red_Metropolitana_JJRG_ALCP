select

    f.abordaje_key,
    f.evento_id,

    -- Usuario
    u.usuario_key,
    u.usuario_id,
    u.cantidad_sistemas,
    u.sistemas_observados,
    u.es_multimodal_aprox,

    -- Modo
    m.modo_key,
    m.modo_codigo,
    m.modo_nombre,

    -- Tiempo
    t.tiempo_key,
    t.minuto_inicio,
    t.fecha,
    t.anio,
    t.mes,
    t.dia,
    t.hora,
    t.minuto,
    t.numero_dia_semana,
    t.dia_semana,
    t.es_dia_habil,
    t.es_hora_pico,

    -- Zona
    z.zona_key,
    z.zona_nombre,

    -- Punto de servicio
    p.punto_servicio_key,
    p.codigo_fuente,
    p.nombre
        as punto_servicio_nombre,
    p.linea_ruta_eje,
    p.latitud,
    p.longitud,

    -- Medidas
    f.cantidad_abordajes,
    f.monto_gtq

from {{ ref('fact_abordajes') }} f

join {{ ref('dim_usuario') }} u
    on f.usuario_key = u.usuario_key

join {{ ref('dim_modo') }} m
    on f.modo_key = m.modo_key

join {{ ref('dim_tiempo') }} t
    on f.tiempo_key = t.tiempo_key

join {{ ref('dim_zona') }} z
    on f.zona_key = z.zona_key

join {{ ref('dim_punto_servicio') }} p
    on f.punto_servicio_key
        = p.punto_servicio_key