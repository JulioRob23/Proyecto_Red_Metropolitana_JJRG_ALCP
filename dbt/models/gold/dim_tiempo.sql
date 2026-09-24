with minutos as (

    select

        generate_series(

            timestamp '2026-06-01 00:00:00',

            timestamp '2026-07-15 23:59:00',

            interval '1 minute'

        ) as instante

)

select

    to_char(
        instante,
        'YYYYMMDDHH24MI'
    )::bigint
        as tiempo_key,

    instante
        as minuto_inicio,

    instante::date
        as fecha,

    extract(
        year from instante
    )::integer
        as anio,

    extract(
        month from instante
    )::integer
        as mes,

    extract(
        day from instante
    )::integer
        as dia,

    extract(
        hour from instante
    )::integer
        as hora,

    extract(
        minute from instante
    )::integer
        as minuto,

    extract(
        isodow from instante
    )::integer
        as numero_dia_semana,

    case extract(
        isodow from instante
    )

        when 1 then 'Lunes'
        when 2 then 'Martes'
        when 3 then 'Miércoles'
        when 4 then 'Jueves'
        when 5 then 'Viernes'
        when 6 then 'Sábado'
        when 7 then 'Domingo'

    end as dia_semana,

    case

        when extract(
            isodow from instante
        ) between 1 and 5
            then true

        else false

    end as es_dia_habil,

    case

        when extract(
            hour from instante
        ) between 6 and 8
            then true

        when extract(
            hour from instante
        ) between 16 and 18
            then true

        else false

    end as es_hora_pico

from minutos