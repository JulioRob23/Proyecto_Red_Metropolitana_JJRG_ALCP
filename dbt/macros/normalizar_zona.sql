{% macro normalizar_zona(campo) %}

case

    when {{ campo }} is null
      or trim({{ campo }}) = ''
        then null

    -- Z10 -> Zona 10
    when upper(trim({{ campo }})) ~ '^Z[0-9]+$'
        then
            'Zona ' ||
            substring(
                upper(trim({{ campo }}))
                from 2
            )

    -- ZONA 10 -> Zona 10
    when upper(trim({{ campo }})) ~ '^ZONA [0-9]+$'
        then
            'Zona ' ||
            regexp_replace(
                upper(trim({{ campo }})),
                '^ZONA ',
                ''
            )

    -- MIXCO -> Mixco
    -- SAN MIGUEL PETAPA -> San Miguel Petapa
    -- VILLA NUEVA -> Villa Nueva
    else
        initcap(
            lower(
                trim({{ campo }})
            )
        )

end

{% endmacro %}