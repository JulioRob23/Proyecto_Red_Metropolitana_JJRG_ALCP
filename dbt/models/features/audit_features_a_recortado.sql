{{ config(materialized='table') }}

{% set cortes_a = [
    ['A', '2026-07-01']
] %}

{{ features_p2_query(
    cortes_a,
    '2026-07-01'
) }}