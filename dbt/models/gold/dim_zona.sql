select

    zona_id::integer
        as zona_key,

    zona_nombre

from {{ ref('dim_zona_conformada') }}