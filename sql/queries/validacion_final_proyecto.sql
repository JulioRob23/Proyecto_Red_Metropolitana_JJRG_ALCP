-- ==========================================================
-- VALIDACION FINAL - PROYECTO RED METROPOLITANA
-- ==========================================================


-- 1. Silver

SELECT
    'Silver - Transmetro' AS objeto,
    COUNT(*) AS filas
FROM silver.silver_transmetro_validaciones

UNION ALL

SELECT
    'Silver - Transurbano',
    COUNT(*)
FROM silver.silver_transurbano_transacciones

UNION ALL

SELECT
    'Silver - MetroRiel',
    COUNT(*)
FROM silver.silver_metroriel_viajes

UNION ALL

SELECT
    'Silver - Aerometro',
    COUNT(*)
FROM silver.silver_aerometro_boardings;


-- 2. Gold

SELECT
    'Gold - dim_modo' AS objeto,
    COUNT(*) AS filas
FROM gold.dim_modo

UNION ALL

SELECT
    'Gold - dim_zona',
    COUNT(*)
FROM gold.dim_zona

UNION ALL

SELECT
    'Gold - dim_usuario',
    COUNT(*)
FROM gold.dim_usuario

UNION ALL

SELECT
    'Gold - dim_tiempo',
    COUNT(*)
FROM gold.dim_tiempo

UNION ALL

SELECT
    'Gold - dim_punto_servicio',
    COUNT(*)
FROM gold.dim_punto_servicio

UNION ALL

SELECT
    'Gold - fact_abordajes',
    COUNT(*)
FROM gold.fact_abordajes

UNION ALL

SELECT
    'Gold - fact_viajes_metroriel',
    COUNT(*)
FROM gold.fact_viajes_metroriel;


-- 3. Cuarentena

SELECT
    'Cuarentena' AS objeto,
    COUNT(*) AS filas
FROM quarantine.registros_invalidos;


-- 4. Features

SELECT
    COUNT(*) AS filas_features,
    COUNT(DISTINCT usuario_id) AS usuarios_features,
    COUNT(*) - COUNT(DISTINCT usuario_id) AS duplicados_usuario
FROM features.features_usuario;


-- 5. Demanda oficial

SELECT
    SUM(cantidad_abordajes) AS demanda_fact
FROM gold.fact_abordajes;


SELECT
    SUM(cantidad_abordajes) AS demanda_vista
FROM gold.vw_abordajes_analitica;


-- 6. Claves nulas de fact_abordajes

SELECT
    COUNT(*) AS claves_nulas_fact_abordajes
FROM gold.fact_abordajes
WHERE usuario_key IS NULL
   OR modo_key IS NULL
   OR tiempo_key IS NULL
   OR zona_key IS NULL
   OR punto_servicio_key IS NULL;


-- 7. Claves nulas de MetroRiel

SELECT
    COUNT(*) AS claves_nulas_fact_viajes
FROM gold.fact_viajes_metroriel
WHERE usuario_key IS NULL
   OR modo_key IS NULL
   OR tiempo_entrada_key IS NULL
   OR tiempo_salida_key IS NULL
   OR zona_origen_key IS NULL
   OR zona_destino_key IS NULL
   OR punto_origen_key IS NULL
   OR punto_destino_key IS NULL;


-- 8. Reglas de calidad

SELECT
    regla_calidad,
    COUNT(*) AS cantidad
FROM quarantine.registros_invalidos
GROUP BY regla_calidad
ORDER BY regla_calidad;