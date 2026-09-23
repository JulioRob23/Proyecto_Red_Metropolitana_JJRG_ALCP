CREATE SCHEMA IF NOT EXISTS catalogos;


-- --------------------------------------------------
-- Usuarios mínimos de Transurbano
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS catalogos.usuarios_transurbano (
    num_tarjeta VARCHAR(50) PRIMARY KEY
);


-- --------------------------------------------------
-- Usuarios mínimos de MetroRiel
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS catalogos.usuarios_metroriel (
    card VARCHAR(50) PRIMARY KEY
);


-- --------------------------------------------------
-- Usuarios mínimos de Aerómetro
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS catalogos.usuarios_aerometro (
    user_hash VARCHAR(50) PRIMARY KEY
);