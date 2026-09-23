select

    t.row_number
        as transaccion_id,

    t.num_tarjeta,
    i.usuario_id,
    t.cod_parada,
    t.ruta,

    t.fecha_hora
        as fecha_hora_local,

    -- Transurbano entrega centavos.
    t.monto_centavos,

    round(
        t.monto_centavos::numeric / 100,
        2
    ) as monto_gtq,

    -- Se conserva el estado entregado por el operador.
    t.cod_estado,

    {{ normalizar_zona('p.sector') }}
        as zona_nombre,

    p.descripcion
        as parada_nombre,

    t.ingested_at,
    t.source_file,
    t.source_sha256

from {{ ref('stg_transurbano') }} t

left join {{ ref('stg_tu_paradas') }} p
    on t.cod_parada = p.cod_parada
    
left join {{ ref('bridge_identidad_usuarios') }} i
    on i.sistema = 'TRANSURBANO'
    and i.clave_fuente = t.num_tarjeta
where t.cod_parada is not null

  and t.fecha_hora
      <= timestamp '2026-07-15 23:59:59'


      