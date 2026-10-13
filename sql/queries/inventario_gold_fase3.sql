-- ==========================================================
-- INVENTARIO GOLD - FASE 3
-- ==========================================================


-- 1. Relaciones existentes dentro del esquema Gold

SELECT
    n.nspname AS esquema,
    c.relname AS relacion,

    CASE c.relkind
        WHEN 'r' THEN 'tabla'
        WHEN 'v' THEN 'vista'
        WHEN 'm' THEN 'vista_materializada'
        ELSE c.relkind::text
    END AS tipo

FROM pg_class c

JOIN pg_namespace n
    ON n.oid = c.relnamespace

WHERE n.nspname = 'gold'
  AND c.relkind IN ('r', 'v', 'm')

ORDER BY
    tipo,
    relacion;


-- 2. Inventario de campos

SELECT
    table_name AS relacion,
    ordinal_position AS posicion,
    column_name AS campo,
    data_type AS tipo_dato,
    is_nullable AS permite_nulos

FROM information_schema.columns

WHERE table_schema = 'gold'

ORDER BY
    table_name,
    ordinal_position;


-- 3. Conteos de las tablas principales Gold

SELECT
    'dim_modo' AS relacion,
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
FROM gold.dim_punto_servicio

UNION ALL

SELECT
    'fact_abordajes',
    COUNT(*)
FROM gold.fact_abordajes

UNION ALL

SELECT
    'fact_viajes_metroriel',
    COUNT(*)
FROM gold.fact_viajes_metroriel

ORDER BY relacion;