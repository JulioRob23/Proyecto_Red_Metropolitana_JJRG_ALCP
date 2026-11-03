{{ config(materialized='table') }}

{% set fecha_corte_var = var('fecha_corte', none) %}

{% if fecha_corte_var is none %}

    {% set cortes = [
        ['A', '2026-07-01'],
        ['B', '2026-07-31'],
        ['C', '2026-08-30']
    ] %}

{% else %}

    {# Convertimos el valor recibido explícitamente a texto #}
    {% set fecha_corte = fecha_corte_var | string | trim %}

    {% if fecha_corte == '2026-07-01' %}

        {% set cortes = [
            ['A', '2026-07-01']
        ] %}

    {% elif fecha_corte == '2026-07-31' %}

        {% set cortes = [
            ['B', '2026-07-31']
        ] %}

    {% elif fecha_corte == '2026-08-30' %}

        {% set cortes = [
            ['C', '2026-08-30']
        ] %}

    {% else %}

        {{ exceptions.raise_compiler_error(
            "fecha_corte no válida: "
            ~ fecha_corte
            ~ ". Use 2026-07-01, "
            ~ "2026-07-31 o "
            ~ "2026-08-30."
        ) }}

    {% endif %}

{% endif %}

{{ features_p2_query(cortes) }}