select *
from {{ ref('features_usuario') }}

where

    eventos_7d > eventos_30d

    or eventos_30d > eventos_periodo

    or proporcion_hora_pico < 0
    or proporcion_hora_pico > 1

    or proporcion_dia_habil < 0
    or proporcion_dia_habil > 1

    or dias_desde_ultima_actividad < 0  