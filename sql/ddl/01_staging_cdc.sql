CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS cdc;


-- --------------------------------------------------
-- Staging temporal del log CDC
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS staging.cdc_padron_eventos (
    seq BIGINT,
    commit_ts TIMESTAMP,
    op VARCHAR(10),
    tarjeta VARCHAR(50),
    perfil VARCHAR(50),
    zona_residencia VARCHAR(100),
    estado VARCHAR(30),

    tipo_llave VARCHAR(30),

    _ingested_at TIMESTAMPTZ,
    _source_file VARCHAR(255),
    _source_sha256 VARCHAR(64)
);


-- --------------------------------------------------
-- Estado vigente del padrón de Transmetro
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS cdc.padron_transmetro_vigente (
    tarjeta VARCHAR(50) PRIMARY KEY,

    perfil VARCHAR(50),
    zona_residencia VARCHAR(100),

    estado VARCHAR(30) NOT NULL,
    activo BOOLEAN NOT NULL,

    ultima_seq BIGINT NOT NULL,
    ultima_op VARCHAR(10) NOT NULL,
    ultimo_commit_ts TIMESTAMP
);