CREATE SCHEMA IF NOT EXISTS staging;


-- ==================================================
-- CATÁLOGOS
-- ==================================================

CREATE TABLE IF NOT EXISTS staging.tm_estaciones_raw (
    estacion_id TEXT,
    nombre TEXT,
    linea TEXT,
    zona TEXT,
    lat TEXT,
    lon TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.tu_paradas_raw (
    cod_parada TEXT,
    descripcion TEXT,
    ruta TEXT,
    sector TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.mr_estaciones_raw (
    id_estacion TEXT,
    nombre_estacion TEXT,
    zona_nombre TEXT,
    km TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.am_estaciones_raw (
    station_code TEXT,
    station_name TEXT,
    axis TEXT,
    district TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


-- ==================================================
-- OPERACIÓN
-- ==================================================

CREATE TABLE IF NOT EXISTS staging.transmetro_validaciones_raw (
    validacion_id TEXT,
    tarjeta TEXT,
    estacion_id TEXT,
    linea TEXT,
    fecha_hora TEXT,
    tarifa TEXT,
    tipo TEXT,
    _row_number TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.transurbano_transacciones_raw (
    fecha TEXT,
    hora TEXT,
    num_tarjeta TEXT,
    cod_parada TEXT,
    ruta TEXT,
    monto_centavos TEXT,
    cod_estado TEXT,
    _row_number TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.metroriel_viajes_raw (
    _line_number TEXT,
    raw_json TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);


CREATE TABLE IF NOT EXISTS staging.aerometro_boardings_raw (
    boarding_id TEXT,
    user_hash TEXT,
    station_code TEXT,
    axis TEXT,
    timestamp_utc TEXT,
    cabin_number TEXT,
    fare TEXT,
    _row_number TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);

-- ==================================================
-- CDC PARA HISTORIZACIÓN SCD TIPO 2
-- ==================================================

CREATE TABLE IF NOT EXISTS staging.cdc_padron_raw (
    seq TEXT,
    commit_ts TEXT,
    op TEXT,
    tarjeta TEXT,
    perfil TEXT,
    zona_residencia TEXT,
    estado TEXT,
    _ingested_at TEXT,
    _source_file TEXT,
    _source_sha256 TEXT
);