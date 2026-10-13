-- ==========================================================
-- VALIDACIÓN DE GOBERNANZA Y CALIDAD - FASE 3
-- ==========================================================


-- 1. Registros de cuarentena por regla

SELECT
    regla_calidad,
    COUNT(*) AS cantidad
FROM quarantine.registros_invalidos
GROUP BY regla_calidad
ORDER BY regla_calidad;


-- 2. Total de cuarentena

SELECT
    COUNT(*) AS total_cuarentena
FROM quarantine.registros_invalidos;


-- 3. Volumen Silver por operador

SELECT
    'Transmetro' AS fuente,
    COUNT(*) AS filas_silver
FROM silver.silver_transmetro_validaciones

UNION ALL

SELECT
    'Transurbano',
    COUNT(*)
FROM silver.silver_transurbano_transacciones

UNION ALL

SELECT
    'MetroRiel',
    COUNT(*)
FROM silver.silver_metroriel_viajes

UNION ALL

SELECT
    'Aerometro',
    COUNT(*)
FROM silver.silver_aerometro_boardings

ORDER BY fuente;


-- 4. Verificación de duplicados en las claves principales de Silver

SELECT
    'Transmetro' AS fuente,
    COUNT(*) - COUNT(DISTINCT validacion_id) AS duplicados
FROM silver.silver_transmetro_validaciones

UNION ALL

SELECT
    'Transurbano',
    COUNT(*) - COUNT(DISTINCT transaccion_id)
FROM silver.silver_transurbano_transacciones

UNION ALL

SELECT
    'MetroRiel',
    COUNT(*) - COUNT(DISTINCT trip_id)
FROM silver.silver_metroriel_viajes

UNION ALL

SELECT
    'Aerometro',
    COUNT(*) - COUNT(DISTINCT boarding_id)
FROM silver.silver_aerometro_boardings

ORDER BY fuente;    