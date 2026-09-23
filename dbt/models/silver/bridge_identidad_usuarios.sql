with claves as (

    -- ==================================================
    -- TRANSMETRO
    -- ==================================================

    select distinct

        'TRANSMETRO'::text as sistema,
        tarjeta as clave_fuente,

        lpad(
            (
                substring(
                    tarjeta
                    from '^TC-([0-9]{8})$'
                )::bigint
            )::text,
            8,
            '0'
        ) as nucleo_numerico,

        'NUCLEO_NUMERICO'::text
            as metodo_identidad

    from {{ ref('stg_transmetro') }}

    where tarjeta ~ '^TC-[0-9]{8}$'


    union


    -- También incluimos tarjetas observadas en CDC.

    select distinct

        'TRANSMETRO'::text,
        tarjeta,

        lpad(
            (
                substring(
                    tarjeta
                    from '^TC-([0-9]{8})$'
                )::bigint
            )::text,
            8,
            '0'
        ),

        'NUCLEO_NUMERICO'::text

    from {{ ref('stg_cdc_padron') }}

    where tarjeta ~ '^TC-[0-9]{8}$'


    union


    -- ==================================================
    -- TRANSURBANO
    -- ==================================================

    select distinct

        'TRANSURBANO'::text,
        num_tarjeta,

        lpad(
            (num_tarjeta::bigint)::text,
            8,
            '0'
        ),

        'NUCLEO_NUMERICO'::text

    from {{ ref('stg_transurbano') }}

    where num_tarjeta ~ '^[0-9]{10}$'


    union


    -- ==================================================
    -- METRORIEL
    -- ==================================================

    select distinct

        'METRORIEL'::text,
        card,

        lpad(
            (
                substring(
                    card
                    from '^MR([0-9]{7})$'
                )::bigint
            )::text,
            8,
            '0'
        ),

        'NUCLEO_NUMERICO'::text

    from {{ ref('stg_metroriel') }}

    where card ~ '^MR[0-9]{7}$'


    union


    -- ==================================================
    -- AERÓMETRO
    -- ==================================================

    select distinct

        'AEROMETRO'::text,
        user_hash,
        null::text,

        'AISLADO_SIN_CROSSWALK'::text

    from {{ ref('stg_aerometro') }}

    where user_hash is not null

),

identidades as (

    select

        sistema,
        clave_fuente,
        nucleo_numerico,
        metodo_identidad,

        case

            when sistema = 'AEROMETRO'
            then encode(
                digest(
                    'AEROMETRO|' || clave_fuente,
                    'sha256'
                ),
                'hex'
            )

            else encode(
                digest(
                    'NUMERICO|' || nucleo_numerico,
                    'sha256'
                ),
                'hex'
            )

        end as usuario_id

    from claves

)

select *
from identidades