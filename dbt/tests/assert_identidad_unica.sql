select

    sistema,
    clave_fuente,
    count(*) as cantidad

from {{ ref('bridge_identidad_usuarios') }}

group by
    sistema,
    clave_fuente

having count(*) > 1