--
-- PostgreSQL database dump
--

\restrict XoZzhGEY6MPeNAc0kLeQ7EnRnA3rwrq9QMYsBIcZJAZuarIX0p1dEFVjSRra9gN

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: gold; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA gold;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dim_modo; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.dim_modo (
    modo_key integer,
    modo_codigo text,
    modo_nombre text
);


--
-- Name: dim_punto_servicio; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.dim_punto_servicio (
    punto_servicio_key bigint,
    modo_key integer,
    modo_codigo text,
    codigo_fuente text,
    nombre text,
    linea_ruta_eje text,
    zona_key integer,
    zona_nombre text,
    latitud numeric,
    longitud numeric
);


--
-- Name: dim_tiempo; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.dim_tiempo (
    tiempo_key bigint,
    minuto_inicio timestamp without time zone,
    fecha date,
    anio integer,
    mes integer,
    dia integer,
    hora integer,
    minuto integer,
    numero_dia_semana integer,
    dia_semana text,
    es_dia_habil boolean,
    es_hora_pico boolean
);


--
-- Name: dim_usuario; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.dim_usuario (
    usuario_key bigint,
    usuario_id text,
    cantidad_sistemas bigint,
    sistemas_observados text,
    es_multimodal_aprox boolean,
    identidad_aislada boolean
);


--
-- Name: dim_zona; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.dim_zona (
    zona_key integer,
    zona_nombre text
);


--
-- Name: fact_abordajes; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.fact_abordajes (
    abordaje_key bigint,
    usuario_key bigint,
    modo_key integer,
    tiempo_key bigint,
    zona_key integer,
    punto_servicio_key bigint,
    evento_id text,
    cantidad_abordajes integer,
    monto_gtq numeric
);


--
-- Name: fact_viajes_metroriel; Type: TABLE; Schema: gold; Owner: -
--

CREATE TABLE gold.fact_viajes_metroriel (
    viaje_key bigint,
    trip_id bigint,
    usuario_key bigint,
    modo_key integer,
    tiempo_entrada_key bigint,
    tiempo_salida_key bigint,
    zona_origen_key integer,
    zona_destino_key integer,
    punto_origen_key bigint,
    punto_destino_key bigint,
    cantidad_viajes integer,
    tarifa_gtq numeric(10,2),
    duracion_segundos integer
);


--
-- PostgreSQL database dump complete
--

\unrestrict XoZzhGEY6MPeNAc0kLeQ7EnRnA3rwrq9QMYsBIcZJAZuarIX0p1dEFVjSRra9gN

