-- ==========================================================
-- VALIDACIÓN DE TABLEAU - FASE 2.1
-- ==========================================================


-- 1. Demanda total y por modo
SELECT
    modo_nombre,
    SUM(cantidad_abordajes) AS abordajes
FROM gold.vw_abordajes_analitica
GROUP BY modo_nombre
ORDER BY abordajes DESC;


-- 2. Total general
SELECT
    SUM(cantidad_abordajes) AS abordajes_totales
FROM gold.vw_abordajes_analitica;


-- 3. Demanda por hora pico
SELECT
    CASE
        WHEN es_hora_pico THEN 'Hora pico'
        ELSE 'Fuera de hora pico'
    END AS tipo_horario,

    SUM(cantidad_abordajes) AS abordajes,

    ROUND(
        100.0 * SUM(cantidad_abordajes)
        / SUM(SUM(cantidad_abordajes)) OVER (),
        2
    ) AS porcentaje

FROM gold.vw_abordajes_analitica

GROUP BY es_hora_pico
ORDER BY tipo_horario;


-- 4. Cobertura por zona
SELECT
    zona_nombre,
    cantidad_puntos_servicio,
    cantidad_modos,
    nivel_cobertura,
    abordajes_totales
FROM gold.vw_cobertura_zonas
ORDER BY abordajes_totales DESC;


-- 5. Zonas sin servicio
SELECT
    COUNT(*) AS zonas_sin_servicio
FROM gold.vw_cobertura_zonas
WHERE tiene_servicio = false;


-- 6. Multimodalidad
SELECT
    nivel_multimodalidad,
    COUNT(*) AS usuarios
FROM gold.vw_usuarios_multimodales
GROUP BY nivel_multimodalidad
ORDER BY usuarios DESC;


-- 7. Usuarios multimodales aproximados
SELECT
    COUNT(*) FILTER (
        WHERE es_multimodal_aprox = true
    ) AS usuarios_multimodales,

    COUNT(*) AS usuarios_totales,

    ROUND(
        100.0
        * COUNT(*) FILTER (
            WHERE es_multimodal_aprox = true
        )
        / COUNT(*),
        2
    ) AS porcentaje_multimodal

FROM gold.vw_usuarios_multimodales;


-- 8. Demanda corredor MetroRiel
SELECT
    CASE
        WHEN pertenece_corredor_metroriel
            THEN 'Corredor MetroRiel'
        ELSE 'Fuera del corredor'
    END AS tipo_zona,

    SUM(abordajes_totales) AS abordajes,

    ROUND(
        100.0 * SUM(abordajes_totales)
        / SUM(SUM(abordajes_totales)) OVER (),
        2
    ) AS porcentaje

FROM gold.vw_metroriel_demanda

GROUP BY pertenece_corredor_metroriel
ORDER BY pertenece_corredor_metroriel DESC;