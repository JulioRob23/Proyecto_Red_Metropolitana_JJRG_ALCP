select *
from (
    values

        (1, 'TRANSMETRO', 'Transmetro'),
        (2, 'TRANSURBANO', 'Transurbano'),
        (3, 'METRORIEL', 'MetroRiel'),
        (4, 'AEROMETRO', 'Aerómetro')

) as modos (
    modo_key,
    modo_codigo,
    modo_nombre
)