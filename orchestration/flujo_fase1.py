from pathlib import Path
from datetime import datetime
import glob
import json
import os
import shutil
import subprocess
import sys
import time

import psycopg2
import pyarrow.parquet as pq

from dotenv import load_dotenv
from prefect import flow, task, get_run_logger


# ==================================================
# CONFIGURACIÓN
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DBT_DIR = PROJECT_ROOT / "dbt"

CORRIDAS_DIR = (
    PROJECT_ROOT
    / "docs"
    / "metricas"
    / "corridas"
)

CORRIDAS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

os.environ["DBT_PROFILES_DIR"] = str(DBT_DIR)


# ==================================================
# UTILIDADES
# ==================================================

def ejecutar_comando(comando, nombre):
    """
    Ejecuta un comando y muestra su salida.
    Si falla, detiene el pipeline.
    """

    logger = get_run_logger()

    logger.info(
        f"Iniciando: {nombre}"
    )

    inicio = time.perf_counter()

    resultado = subprocess.run(
        comando,
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(resultado.stderr)

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falló el proceso: {nombre}"
        )

    duracion = round(
        time.perf_counter() - inicio,
        2
    )

    logger.info(
        f"Finalizado: {nombre} "
        f"({duracion} segundos)"
    )

    return duracion


def conectar_postgres():

    return psycopg2.connect(
        host=os.getenv(
            "POSTGRES_HOST",
            "localhost"
        ),
        port=int(
            os.getenv(
                "POSTGRES_PORT",
                "5433"
            )
        ),
        dbname=os.getenv(
            "POSTGRES_DB",
            "red_metropolitana"
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "red_user"
        ),
        password=os.getenv(
            "POSTGRES_PASSWORD"
        )
    )


def contar_parquet(carpeta):

    patron = str(
        PROJECT_ROOT
        / "lake"
        / "bronze"
        / carpeta
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(
        patron
    )

    return sum(
        pq.ParquetFile(
            archivo
        ).metadata.num_rows
        for archivo in archivos
    )


# ==================================================
# INFRAESTRUCTURA
# ==================================================

@task
def verificar_infraestructura():

    return ejecutar_comando(
        [
            "docker",
            "compose",
            "up",
            "-d"
        ],
        "Infraestructura Docker"
    )


# ==================================================
# INGESTA BRONZE
# ==================================================

@task
def ingesta_batch():

    duracion_catalogos = ejecutar_comando(
        [
            sys.executable,
            "ingestion/batch/"
            "cargar_catalogos_bronze.py"
        ],
        "Batch de catálogos"
    )

    duracion_metroriel = ejecutar_comando(
        [
            sys.executable,
            "ingestion/batch/"
            "cargar_metroriel_bronze.py"
        ],
        "Batch de MetroRiel"
    )

    return (
        duracion_catalogos
        + duracion_metroriel
    )


@task
def ingesta_transmetro():

    productor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "producer_transmetro.py"
        ],
        "Producer Transmetro"
    )

    consumidor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "consumer_transmetro_bronze.py"
        ],
        "Consumer Transmetro"
    )

    return productor + consumidor


@task
def ingesta_transurbano():

    productor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "producer_transurbano.py"
        ],
        "Producer Transurbano"
    )

    consumidor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "consumer_transurbano_bronze.py"
        ],
        "Consumer Transurbano"
    )

    return productor + consumidor


@task
def ingesta_aerometro():

    productor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "producer_aerometro.py"
        ],
        "Producer Aerómetro"
    )

    consumidor = ejecutar_comando(
        [
            sys.executable,
            "ingestion/streaming/"
            "consumer_aerometro_bronze.py"
        ],
        "Consumer Aerómetro"
    )

    return productor + consumidor


@task
def ingesta_cdc():

    return ejecutar_comando(
        [
            sys.executable,
            "ingestion/cdc/"
            "cargar_cdc_bronze.py"
        ],
        "CDC → Bronze"
    )


# ==================================================
# STAGING
# ==================================================

@task
def cargar_staging():

    return ejecutar_comando(
        [
            sys.executable,
            "staging/"
            "cargar_bronze_a_staging.py"
        ],
        "Bronze → Staging"
    )


# ==================================================
# DBT
# ==================================================

@task
def ejecutar_dbt():

    dbt = shutil.which("dbt")

    if dbt is None:
        raise RuntimeError(
            "No se encontró dbt."
        )

    return ejecutar_comando(
        [
            dbt,
            "run",
            "--project-dir",
            "dbt"
        ],
        "dbt run"
    )


@task
def ejecutar_tests():

    dbt = shutil.which("dbt")

    if dbt is None:
        raise RuntimeError(
            "No se encontró dbt."
        )

    return ejecutar_comando(
        [
            dbt,
            "test",
            "--project-dir",
            "dbt"
        ],
        "dbt test"
    )


# ==================================================
# MÉTRICAS
# ==================================================

@task
def generar_metricas():

    duracion_bronze = ejecutar_comando(
        [
            sys.executable,
            "ingestion/"
            "verificar_conteos_bronze.py"
        ],
        "Métricas Bronze"
    )

    duracion_silver = ejecutar_comando(
        [
            sys.executable,
            "staging/"
            "generar_metricas_silver.py"
        ],
        "Métricas Silver"
    )

    return (
        duracion_bronze
        + duracion_silver
    )


# ==================================================
# SNAPSHOT PARA IDEMPOTENCIA
# ==================================================

@task
def guardar_snapshot(tiempos):

    logger = get_run_logger()

    bronze = {
        "tm_estaciones":
            contar_parquet("tm_estaciones"),

        "tu_paradas":
            contar_parquet("tu_paradas"),

        "mr_estaciones":
            contar_parquet("mr_estaciones"),

        "am_estaciones":
            contar_parquet("am_estaciones"),

        "transmetro":
            contar_parquet("transmetro"),

        "transurbano":
            contar_parquet("transurbano"),

        "metroriel":
            contar_parquet("metroriel"),

        "aerometro":
            contar_parquet("aerometro"),

        "cdc_padron":
            contar_parquet("cdc_padron")
    }

    conn = conectar_postgres()

    try:

        cursor = conn.cursor()

        silver_tablas = [
            "silver.silver_transmetro_validaciones",
            "silver.silver_transurbano_transacciones",
            "silver.silver_metroriel_viajes",
            "silver.silver_aerometro_boardings",
            "silver.dim_zona_conformada",
            "silver.bridge_identidad_usuarios",
            "silver.scd2_padron_transmetro"
        ]

        gold_tablas = [
            "gold.dim_modo",
            "gold.dim_zona",
            "gold.dim_usuario",
            "gold.dim_tiempo",
            "gold.dim_punto_servicio",
            "gold.fact_abordajes",
            "gold.fact_viajes_metroriel"
        ]

        silver = {}

        for tabla in silver_tablas:

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {tabla};"
            )

            silver[tabla] = (
                cursor.fetchone()[0]
            )

        gold = {}

        for tabla in gold_tablas:

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {tabla};"
            )

            gold[tabla] = (
                cursor.fetchone()[0]
            )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM quarantine.registros_invalidos;
            """
        )

        cuarentena = (
            cursor.fetchone()[0]
        )

    finally:

        conn.close()

    snapshot = {
        "fecha": datetime.now()
            .astimezone()
            .isoformat(),

        "bronze": bronze,
        "silver": silver,
        "gold": gold,
        "cuarentena": cuarentena,
        
        "tiempos_segundos": tiempos
    }

    nombre = (
        "corrida_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".json"
    )

    ruta = (
        CORRIDAS_DIR
        / nombre
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            snapshot,
            archivo,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"Snapshot guardado: "
        f"{ruta.relative_to(PROJECT_ROOT)}"
    )

    print()
    print("=" * 80)
    print("SNAPSHOT DE CONTEOS")
    print("=" * 80)

    print(
        json.dumps(
            snapshot,
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 80)

    return str(ruta)


# ==================================================
# LIMPIEZA DE STAGING
# ==================================================

@task
def vaciar_staging():

    ruta_sql = (
        PROJECT_ROOT
        / "sql"
        / "ddl"
        / "99_vaciar_staging.sql"
    )

    sql = ruta_sql.read_text(
        encoding="utf-8"
    )

    conn = conectar_postgres()

    try:

        cursor = conn.cursor()

        cursor.execute(sql)

        conn.commit()

        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*)
                 FROM staging.transmetro_validaciones_raw)
              + (SELECT COUNT(*)
                 FROM staging.transurbano_transacciones_raw)
              + (SELECT COUNT(*)
                 FROM staging.metroriel_viajes_raw)
              + (SELECT COUNT(*)
                 FROM staging.aerometro_boardings_raw)
              + (SELECT COUNT(*)
                 FROM staging.cdc_padron_raw);
            """
        )

        filas = cursor.fetchone()[0]

        print(
            f"Staging al finalizar: "
            f"{filas} filas"
        )

        if filas != 0:
            raise RuntimeError(
                "Staging no quedó vacío."
            )

    finally:

        conn.close()

    return filas


# ==================================================
# FLOW PRINCIPAL
# ==================================================

@flow(
    name="Red Metropolitana - Fase 1"
)
def flujo_fase1():

    logger = get_run_logger()

    logger.info(
        "Iniciando pipeline completo "
        "de la Fase 1."
    )

    inicio_total = time.perf_counter()

    tiempos = {}

    tiempos["infraestructura"] = (
        verificar_infraestructura()
    )

    tiempos["batch"] = (
        ingesta_batch()
    )

    tiempos["transmetro"] = (
        ingesta_transmetro()
    )

    tiempos["transurbano"] = (
        ingesta_transurbano()
    )

    tiempos["aerometro"] = (
        ingesta_aerometro()
    )

    tiempos["cdc"] = (
        ingesta_cdc()
    )

    tiempos["staging"] = (
        cargar_staging()
    )

    tiempos["dbt_run"] = (
        ejecutar_dbt()
    )

    tiempos["dbt_test"] = (
        ejecutar_tests()
    )

    tiempos["metricas"] = (
        generar_metricas()
    )

    snapshot = guardar_snapshot(tiempos)

    vaciar_staging()

    duracion_total = round(
        time.perf_counter()
        - inicio_total,
        2
    )

    print()
    print("=" * 80)
    print("PIPELINE COMPLETADO")
    print("=" * 80)

    for etapa, segundos in tiempos.items():

        print(
            f"{etapa:<20}: "
            f"{segundos:>10.2f} s"
        )

    print("-" * 80)

    print(
        f"{'TOTAL':<20}: "
        f"{duracion_total:>10.2f} s"
    )

    print()
    print(
        f"Snapshot: {snapshot}"
    )

    print("=" * 80)

    logger.info(
        "Pipeline finalizado correctamente."
    )


if __name__ == "__main__":
    flujo_fase1() 