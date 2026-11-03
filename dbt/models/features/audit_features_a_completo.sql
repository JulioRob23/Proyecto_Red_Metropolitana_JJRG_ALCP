{{ config(materialized='view') }}

select *

from {{ ref('features_usuario') }}

where corte = 'A'