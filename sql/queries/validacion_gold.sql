-- ==================================================
-- VALIDACIÓN FINAL DE LA CAPA GOLD
-- ==================================================


-- --------------------------------------------------
-- 1. Conteos de dimensiones
-- --------------------------------------------------

SELECT
    'dim_modo' AS tabla,
    COUNT(*) AS filas
FROM gold.dim_modo

UNION ALL

SELECT
    'dim_zona',
    COUNT(*)
FROM gold.dim_zona

UNION ALL

SELECT
    'dim_usuario',
    COUNT(*)
FROM gold.dim_usuario

UNION ALL

SELECT
    'dim_tiempo',
    COUNT(*)
FROM gold.dim_tiempo

UNION ALL

SELECT
    'dim_punto_servicio',
    COUNT(*)
FROM gold.dim_punto_servicio;


-- --------------------------------------------------
-- 2. Conteos de hechos
-- --------------------------------------------------

SELECT
    'fact_abordajes' AS tabla,
    COUNT(*) AS filas
FROM gold.fact_abordajes

UNION ALL

SELECT
    'fact_viajes_metroriel',
    COUNT(*)
FROM gold.fact_viajes_metroriel;


-- --------------------------------------------------
-- 3. Abordajes y monto por modo
-- --------------------------------------------------

SELECT
    m.modo_nombre,
    COUNT(*) AS abordajes,
    ROUND(SUM(f.monto_gtq), 2) AS monto_gtq
FROM gold.fact_abordajes f
JOIN gold.dim_modo m
    ON f.modo_key = m.modo_key
GROUP BY m.modo_nombre
ORDER BY m.modo_nombre;


-- --------------------------------------------------
-- 4. Claves nulas fact_abordajes
-- --------------------------------------------------

SELECT
    COUNT(*) AS claves_nulas_fact_abordajes
FROM gold.fact_abordajes
WHERE usuario_key IS NULL
   OR modo_key IS NULL
   OR tiempo_key IS NULL
   OR zona_key IS NULL
   OR punto_servicio_key IS NULL;


-- --------------------------------------------------
-- 5. Claves nulas fact_viajes_metroriel
-- --------------------------------------------------

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