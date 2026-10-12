select

    usuario_key,
    usuario_id,

    cantidad_sistemas,
    sistemas_observados,
    es_multimodal_aprox,
    identidad_aislada,

    case

        when identidad_aislada
            then 'Identidad aislada'

        when cantidad_sistemas = 1
            then '1 sistema'

        when cantidad_sistemas = 2
            then '2 sistemas'

        when cantidad_sistemas = 3
            then '3 sistemas'

        when cantidad_sistemas >= 4
            then '4 sistemas'

        else 'Sin clasificación'

    end as nivel_multimodalidad

from {{ ref('dim_usuario') }}