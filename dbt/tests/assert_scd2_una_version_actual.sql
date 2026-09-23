select

    tarjeta

from {{ ref('scd2_padron_transmetro') }}

group by tarjeta

having sum(
    case
        when es_actual
            then 1
        else 0
    end
) <> 1