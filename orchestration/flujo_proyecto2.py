from pathlib import Path
from datetime import datetime
import argparse
import csv
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import time

import psycopg2
import pyarrow.parquet as pq

from dotenv import load_dotenv
from prefect import flow, task, get_run_logger


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DBT_DIR = PROJECT_ROOT / "dbt"
INPUT_DIR = PROJECT_ROOT / "datos_red"
RAW_DIR = PROJECT_ROOT / "datos" / "raw"
BRONZE_DIR = PROJECT_ROOT / "lake" / "bronze"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase1"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

os.environ["DBT_PROFILES_DIR"] = str(DBT_DIR)

COMPOSE_PROJECT = "redmetro_p2"


# ============================================================
# ARCHIVOS Y CONTEOS OFICIALES DE PROYECTO 2
# ============================================================

ARCHIVOS_P2 = {
    "aerometro_boardings.csv": {
        "bronze": "aerometro",
        "esperadas": 387053,
    },
    "am_estaciones.csv": {
        "bronze": "am_estaciones",
        "esperadas": 14,
    },
    "cdc_padron_usuarios.csv": {
        "bronze": "cdc_padron",
        "esperadas": 77636,
    },
    "metroriel_viajes.jsonl": {
        "bronze": "metroriel",
        "esperadas": 590844,
    },
    "mr_estaciones.csv": {
        "bronze": "mr_estaciones",
        "esperadas": 22,
    },
    "tm_estaciones.csv": {
        "bronze": "tm_estaciones",
        "esperadas": 104,
    },
    "transmetro_validaciones.csv": {
        "bronze": "transmetro",
        "esperadas": 713786,
    },
    "transurbano_transacciones.csv": {
        "bronze": "transurbano",
        "esperadas": 1635788,
    },
    "tu_paradas.csv": {
        "bronze": "tu_paradas",
        "esperadas": 328,
    },
}


# ============================================================
# UTILIDADES
# ============================================================

def ejecutar_comando(comando, nombre):
    """
    Ejecuta un comando desde la raíz del proyecto.
    Si falla, detiene el pipeline.
    """

    logger = get_run_logger()

    logger.info(f"Iniciando: {nombre}")

    inicio = time.perf_counter()

    resultado = subprocess.run(
        comando,
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )

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
        f"({duracion:.2f} segundos)"
    )

    return duracion

def detener_proceso(proceso):

    if proceso is None:
        return

    if proceso.poll() is None:

        proceso.terminate()

        try:
            proceso.wait(timeout=10)

        except subprocess.TimeoutExpired:

            proceso.kill()
            proceso.wait()


def ejecutar_streaming_concurrente(
    productor_script,
    consumidor_script,
    nombre,
    timeout_consumer=1800,
):

    logger = get_run_logger()

    logger.info(
        f"Iniciando streaming concurrente: {nombre}"
    )

    inicio = time.perf_counter()

    env = os.environ.copy()

    consumidor = None
    productor = None

    try:

        # El consumer queda listo primero.
        consumidor = subprocess.Popen(
            [
                sys.executable,
                "-u",
                consumidor_script,
            ],
            cwd=PROJECT_ROOT,
            env=env,
        )

        time.sleep(3)

        # Si murió antes de empezar el producer,
        # tenemos un problema real.
        if consumidor.poll() is not None:

            raise RuntimeError(
                f"El consumer de {nombre} "
                "terminó antes de iniciar el producer."
            )

        productor = subprocess.Popen(
            [
                sys.executable,
                "-u",
                productor_script,
            ],
            cwd=PROJECT_ROOT,
            env=env,
        )

        # Esperamos al producer, vigilando también
        # que el consumer no falle.
        while productor.poll() is None:

            rc_consumer = consumidor.poll()

            if (
                rc_consumer is not None
                and rc_consumer != 0
            ):

                detener_proceso(productor)

                raise RuntimeError(
                    f"Falló el consumer de {nombre} "
                    f"con código {rc_consumer}."
                )

            time.sleep(1)

        if productor.returncode != 0:

            detener_proceso(consumidor)

            raise RuntimeError(
                f"Falló el producer de {nombre} "
                f"con código {productor.returncode}."
            )

        # El producer ya envió END.
        # Damos tiempo al consumer para terminar
        # de escribir los últimos chunks.
        try:

            rc_consumer = consumidor.wait(
                timeout=timeout_consumer
            )

        except subprocess.TimeoutExpired:

            detener_proceso(consumidor)

            raise RuntimeError(
                f"El consumer de {nombre} "
                "no terminó después de recibir "
                "la publicación completa."
            )

        if rc_consumer != 0:

            raise RuntimeError(
                f"Falló el consumer de {nombre} "
                f"con código {rc_consumer}."
            )

    except Exception:

        detener_proceso(productor)
        detener_proceso(consumidor)

        raise

    duracion = round(
        time.perf_counter() - inicio,
        2
    )

    logger.info(
        f"Streaming {nombre} completado "
        f"({duracion:.2f} segundos)"
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
        ),
    )


def contar_parquet(carpeta):

    patron = str(
        BRONZE_DIR
        / carpeta
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(patron)

    return sum(
        pq.ParquetFile(
            archivo
        ).metadata.num_rows
        for archivo in archivos
    )


# ============================================================
# VALIDACIONES INICIALES
# ============================================================

@task
def validar_configuracion():

    requeridas = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "KAFKA_BOOTSTRAP_SERVERS",
    ]

    faltantes = [
        variable
        for variable in requeridas
        if not os.getenv(variable)
    ]

    if faltantes:
        raise RuntimeError(
            "Faltan variables en .env: "
            + ", ".join(faltantes)
        )

    print("[OK] Variables de entorno completas.")

    return True


@task
def validar_archivos_entrada():

    faltantes = []

    for archivo in ARCHIVOS_P2:

        ruta = INPUT_DIR / archivo

        if not ruta.exists():
            faltantes.append(archivo)

    if faltantes:

        raise RuntimeError(
            "Faltan archivos de Proyecto 2: "
            + ", ".join(faltantes)
        )

    print()
    print("=" * 70)
    print("ARCHIVOS PROYECTO 2")
    print("=" * 70)

    for archivo in ARCHIVOS_P2:

        ruta = INPUT_DIR / archivo

        print(
            f"{archivo:<38} "
            f"{ruta.stat().st_size:>15,} bytes"
        )

    print("=" * 70)

    print(
        f"[OK] {len(ARCHIVOS_P2)} "
        "archivos requeridos encontrados."
    )

    return True


# ============================================================
# RESET DESDE CERO
# ============================================================

@task
def resetear_entorno_p2():

    logger = get_run_logger()

    logger.info(
        "Eliminando únicamente el estado generado "
        "por Proyecto 2."
    )

    inicio = time.perf_counter()

    # Detiene y elimina contenedores/volúmenes
    # pertenecientes al proyecto Compose de P2.
    subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            COMPOSE_PROJECT,
            "down",
            "-v",
            "--remove-orphans",
        ],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )

    # Lake generado
    lake = PROJECT_ROOT / "lake"

    if lake.exists():
        shutil.rmtree(lake)

    # Artefactos dbt reconstruibles
    for carpeta in [
        DBT_DIR / "target",
        DBT_DIR / "logs",
    ]:

        if carpeta.exists():
            shutil.rmtree(carpeta)

    # Carpeta raw interna
    if RAW_DIR.exists():

        for elemento in RAW_DIR.iterdir():

            if elemento.is_file():
                elemento.unlink()

            elif elemento.is_dir():
                shutil.rmtree(elemento)

    duracion = round(
        time.perf_counter() - inicio,
        2
    )

    logger.info(
        f"Reset P2 completado "
        f"({duracion:.2f} segundos)"
    )

    return duracion


# ============================================================
# PREPARAR ARCHIVOS RAW
# ============================================================

@task
def preparar_datos_raw():

    logger = get_run_logger()

    inicio = time.perf_counter()

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Evita mezclar datos anteriores.
    for elemento in RAW_DIR.iterdir():

        if elemento.is_file():
            elemento.unlink()

        elif elemento.is_dir():
            shutil.rmtree(elemento)

    for archivo in ARCHIVOS_P2:

        origen = INPUT_DIR / archivo
        destino = RAW_DIR / archivo

        shutil.copy2(
            origen,
            destino
        )

    logger.info(
        f"Copiados {len(ARCHIVOS_P2)} "
        "archivos a datos/raw."
    )

    duracion = round(
        time.perf_counter() - inicio,
        2
    )

    return duracion


# ============================================================
# INFRAESTRUCTURA
# ============================================================

@task
def levantar_infraestructura():

    return ejecutar_comando(
        [
            "docker",
            "compose",
            "-p",
            COMPOSE_PROJECT,
            "up",
            "-d",
        ],
        "Infraestructura Docker P2",
    )


@task
def esperar_servicios():

    logger = get_run_logger()

    inicio = time.perf_counter()

    # PostgreSQL
    postgres_ok = False

    for intento in range(60):

        try:

            conn = conectar_postgres()
            conn.close()

            postgres_ok = True
            break

        except Exception:

            time.sleep(2)

    if not postgres_ok:

        raise RuntimeError(
            "PostgreSQL no estuvo disponible "
            "después de 120 segundos."
        )

    logger.info(
        "PostgreSQL disponible."
    )

    # Kafka
    kafka_host = "localhost"
    kafka_port = 9092

    kafka_ok = False

    for intento in range(60):

        try:

            with socket.create_connection(
                (kafka_host, kafka_port),
                timeout=2,
            ):
                kafka_ok = True
                break

        except OSError:

            time.sleep(2)

    if not kafka_ok:

        raise RuntimeError(
            "Kafka no estuvo disponible "
            "después de 120 segundos."
        )

    # Pequeña espera adicional para que
    # el broker termine su inicialización.
    time.sleep(3)

    logger.info(
        "Kafka disponible."
    )

    return round(
        time.perf_counter() - inicio,
        2
    )


# ============================================================
# INICIALIZACIÓN DE POSTGRESQL
# ============================================================

@task
def inicializar_base_datos():

    logger = get_run_logger()

    inicio = time.perf_counter()

    ddl = [
        "01_staging_cdc.sql",
        "02_catalogos_usuarios.sql",
        "03_staging_operacional.sql",
        "04_pgcrypto.sql",
    ]

    conn = conectar_postgres()

    try:

        conn.autocommit = True

        cursor = conn.cursor()

        for archivo in ddl:

            ruta = (
                PROJECT_ROOT
                / "sql"
                / "ddl"
                / archivo
            )

            logger.info(
                f"Ejecutando DDL: {archivo}"
            )

            sql = ruta.read_text(
                encoding="utf-8"
            )

            cursor.execute(sql)

        cursor.close()

    finally:

        conn.close()

    duracion = round(
        time.perf_counter() - inicio,
        2
    )

    logger.info(
        "Base inicializada correctamente."
    )

    return duracion


# ============================================================
# INGESTA
# ============================================================

@task
def ingesta_batch():

    inicio = time.perf_counter()

    ejecutar_comando(
        [
            sys.executable,
            "ingestion/batch/"
            "cargar_catalogos_bronze.py",
        ],
        "Batch de catálogos",
    )

    ejecutar_comando(
        [
            sys.executable,
            "ingestion/batch/"
            "cargar_metroriel_bronze.py",
        ],
        "Batch de MetroRiel",
    )

    return round(
        time.perf_counter() - inicio,
        2
    )


@task
def ingesta_transmetro():

    return ejecutar_streaming_concurrente(
        "ingestion/streaming/"
        "producer_transmetro.py",

        "ingestion/streaming/"
        "consumer_transmetro_bronze.py",

        "Transmetro",
    )


@task
def ingesta_transurbano():

    return ejecutar_streaming_concurrente(
        "ingestion/streaming/"
        "producer_transurbano.py",

        "ingestion/streaming/"
        "consumer_transurbano_bronze.py",

        "Transurbano",
        timeout_consumer=3600,
    )


@task
def ingesta_aerometro():

    return ejecutar_streaming_concurrente(
        "ingestion/streaming/"
        "producer_aerometro.py",

        "ingestion/streaming/"
        "consumer_aerometro_bronze.py",

        "Aerómetro",
    )


@task
def ingesta_cdc():

    return ejecutar_comando(
        [
            sys.executable,
            "ingestion/cdc/"
            "cargar_cdc_bronze.py",
        ],
        "CDC → Bronze",
    )


# ============================================================
# VALIDACIÓN BRONZE
# ============================================================

@task
def validar_conteos_bronze():

    logger = get_run_logger()

    inicio = time.perf_counter()

    resultados = []

    print()
    print("=" * 84)
    print("VALIDACIÓN DE CONTEOS BRONZE - PROYECTO 2")
    print("=" * 84)

    print(
        f"{'Archivo':<38}"
        f"{'Esperadas':>14}"
        f"{'Cargadas':>14}"
        f"{'Diferencia':>14}"
    )

    print("-" * 84)

    errores = []

    for archivo, info in ARCHIVOS_P2.items():

        esperadas = info["esperadas"]

        cargadas = contar_parquet(
            info["bronze"]
        )

        diferencia = (
            cargadas - esperadas
        )

        resultados.append(
            {
                "archivo": archivo,
                "filas_esperadas": esperadas,
                "filas_cargadas": cargadas,
                "diferencia": diferencia,
            }
        )

        print(
            f"{archivo:<38}"
            f"{esperadas:>14,}"
            f"{cargadas:>14,}"
            f"{diferencia:>14,}"
        )

        if diferencia != 0:

            errores.append(
                archivo
            )

    print("=" * 84)

    # CSV entregable
    ruta_csv = (
        OUTPUT_DIR
        / "conteos_bronze_p2.csv"
    )

    with open(
        ruta_csv,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo_csv:

        writer = csv.DictWriter(
            archivo_csv,
            fieldnames=[
                "archivo",
                "filas_esperadas",
                "filas_cargadas",
                "diferencia",
            ],
        )

        writer.writeheader()
        writer.writerows(resultados)

    # Markdown entregable
    ruta_md = (
        OUTPUT_DIR
        / "conteos_bronze_p2.md"
    )

    with open(
        ruta_md,
        "w",
        encoding="utf-8",
    ) as archivo_md:

        archivo_md.write(
            "# Conteos Bronze - Proyecto 2\n\n"
        )

        archivo_md.write(
            "| Archivo | Esperadas | "
            "Cargadas | Diferencia |\n"
        )

        archivo_md.write(
            "|---|---:|---:|---:|\n"
        )

        for fila in resultados:

            archivo_md.write(
                f"| {fila['archivo']} "
                f"| {fila['filas_esperadas']} "
                f"| {fila['filas_cargadas']} "
                f"| {fila['diferencia']} |\n"
            )

    if errores:

        raise RuntimeError(
            "Hay diferencias de conteo "
            "en Bronze: "
            + ", ".join(errores)
        )

    logger.info(
        "Los 9 conteos Bronze coinciden "
        "con los valores esperados."
    )

    return round(
        time.perf_counter() - inicio,
        2
    )


# ============================================================
# STAGING Y CDC
# ============================================================

@task
def cargar_staging():

    return ejecutar_comando(
        [
            sys.executable,
            "staging/"
            "cargar_bronze_a_staging.py",
        ],
        "Bronze → Staging",
    )


@task
def procesar_cdc():

    return ejecutar_comando(
        [
            sys.executable,
            "staging/"
            "procesar_cdc_transmetro.py",
        ],
        "Procesar CDC Transmetro",
    )


@task
def construir_catalogos_usuarios():

    return ejecutar_comando(
        [
            sys.executable,
            "staging/"
            "construir_catalogos_usuarios.py",
        ],
        "Construir catálogos de usuarios",
    )


# ============================================================
# DBT
# ============================================================

@task
def ejecutar_dbt():

    dbt = shutil.which("dbt")

    if dbt is None:

        raise RuntimeError(
            "No se encontró dbt "
            "en el entorno virtual."
        )

    # En 1.1 todavía no construimos las
    # Features P2. Las features antiguas
    # pertenecen al Proyecto 1.
    return ejecutar_comando(
        [
            dbt,
            "run",
            "--project-dir",
            "dbt",
            "--exclude",
            "path:models/features",
        ],
        "dbt run Silver / Quarantine / Gold",
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
            "dbt",
            "--select",
            "path:models/silver",
            "path:models/quarantine",
            "path:models/gold",
            "assert_fact_abordajes_conteo",
            "assert_fact_viajes_metroriel_conteo",
            "assert_identidad_unica",
            "assert_reglas_calidad_silver",
            "assert_scd2_una_version_actual",
        ],
        "dbt test P2 1.1",
    )


# ============================================================
# SNAPSHOT DE WAREHOUSE
# ============================================================

@task
def guardar_snapshot(tiempos):

    conn = conectar_postgres()

    try:

        cursor = conn.cursor()

        tablas = [
            "silver.silver_transmetro_validaciones",
            "silver.silver_transurbano_transacciones",
            "silver.silver_metroriel_viajes",
            "silver.silver_aerometro_boardings",
            "silver.dim_zona_conformada",
            "silver.bridge_identidad_usuarios",
            "silver.scd2_padron_transmetro",
            "gold.dim_modo",
            "gold.dim_zona",
            "gold.dim_usuario",
            "gold.dim_tiempo",
            "gold.dim_punto_servicio",
            "gold.fact_abordajes",
            "gold.fact_viajes_metroriel",
            "quarantine.registros_invalidos",
        ]

        conteos = {}

        for tabla in tablas:

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {tabla};"
            )

            conteos[tabla] = (
                cursor.fetchone()[0]
            )

    finally:

        conn.close()

    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    snapshot = {
        "fecha": datetime.now()
            .astimezone()
            .isoformat(),

        "conteos": conteos,

        "tiempos_segundos": tiempos,
    }

    ruta_json = (
        OUTPUT_DIR
        / f"corrida_{fecha}.json"
    )

    with open(
        ruta_json,
        "w",
        encoding="utf-8",
    ) as archivo:

        json.dump(
            snapshot,
            archivo,
            indent=2,
            ensure_ascii=False,
        )

    ruta_tiempos = (
        OUTPUT_DIR
        / f"tiempos_{fecha}.csv"
    )

    with open(
        ruta_tiempos,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:

        writer = csv.writer(
            archivo
        )

        writer.writerow(
            ["etapa", "segundos"]
        )

        for etapa, segundos in tiempos.items():

            writer.writerow(
                [etapa, segundos]
            )

    print()
    print("=" * 70)
    print("CONTEOS FINALES")
    print("=" * 70)

    for tabla, cantidad in conteos.items():

        print(
            f"{tabla:<48} "
            f"{cantidad:>12,}"
        )

    print("=" * 70)

    return str(ruta_json)


# ============================================================
# VACIAR STAGING AL FINAL
# ============================================================

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

    finally:

        conn.close()

    print(
        "[OK] Staging operacional "
        "vaciado al finalizar."
    )

    return 0


# ============================================================
# FLOW PRINCIPAL
# ============================================================

@flow(
    name="Red Metropolitana - Proyecto 2 - Fase 1.1"
)
def flujo_proyecto2(
    desde_cero=False,
    solo_validar=False,
    reanudar_desde_aerometro=False,
    reanudar_desde_dbt=False,
):
    logger = get_run_logger()

    logger.info(
        "Iniciando Proyecto 2 - Fase 1.1"
    )

    inicio_total = time.perf_counter()

    tiempos = {}

    validar_configuracion()
    validar_archivos_entrada()

    if solo_validar:

        print()
        print("=" * 70)
        print("VALIDACIÓN COMPLETADA")
        print("=" * 70)
        print(
            "El entorno y los archivos "
            "de Proyecto 2 están listos."
        )
        print(
            "No se modificó ninguna base, "
            "lake ni contenedor."
        )
        print("=" * 70)

        return
    
    if reanudar_desde_dbt:

        print()
        print("=" * 80)
        print("REANUDANDO FASE 1.1 DESDE DBT")
        print("=" * 80)

        tiempos["dbt_run"] = (
            ejecutar_dbt()
        )

        tiempos["dbt_test"] = (
            ejecutar_tests()
        )

        snapshot = guardar_snapshot(
            tiempos
        )

        vaciar_staging()

        duracion_total = round(
            time.perf_counter()
            - inicio_total,
            2,
        )

        tiempos["total_reanudacion_dbt"] = (
            duracion_total
        )

        print()
        print("=" * 80)
        print(
            "FASE 1.1 REANUDADA DESDE DBT "
            "Y COMPLETADA"
        )
        print("=" * 80)

        for etapa, segundos in tiempos.items():

            print(
                f"{etapa:<25}: "
                f"{segundos:>12.2f} s"
            )

        print("-" * 80)

        print(
            f"Snapshot: {snapshot}"
        )

        print("=" * 80)

        return
    
    if reanudar_desde_aerometro:

        print()
        print("=" * 80)
        print("REANUDANDO FASE 1.1 DESDE AERÓMETRO")
        print("=" * 80)

        tiempos["aerometro"] = (
            ingesta_aerometro()
        )

        tiempos["cdc_bronze"] = (
            ingesta_cdc()
        )

        tiempos["validacion_bronze"] = (
            validar_conteos_bronze()
        )

        tiempos["staging"] = (
            cargar_staging()
        )

        tiempos["procesar_cdc"] = (
            procesar_cdc()
        )

        tiempos["catalogos_usuarios"] = (
            construir_catalogos_usuarios()
        )

        tiempos["dbt_run"] = (
            ejecutar_dbt()
        )

        tiempos["dbt_test"] = (
            ejecutar_tests()
        )

        snapshot = guardar_snapshot(
            tiempos
        )

        vaciar_staging()

        duracion_total = round(
            time.perf_counter()
            - inicio_total,
            2,
        )

        tiempos["total_reanudacion"] = (
            duracion_total
        )

        print()
        print("=" * 80)
        print(
            "FASE 1.1 REANUDADA Y COMPLETADA"
        )
        print("=" * 80)

        for etapa, segundos in tiempos.items():

            print(
                f"{etapa:<25}: "
                f"{segundos:>12.2f} s"
            )

        print(
            f"Snapshot: {snapshot}"
        )

        print("=" * 80)

        return

    if desde_cero:

        tiempos["reset_p2"] = (
            resetear_entorno_p2()
        )

    tiempos["preparar_raw"] = (
        preparar_datos_raw()
    )

    tiempos["infraestructura"] = (
        levantar_infraestructura()
    )

    tiempos["espera_servicios"] = (
        esperar_servicios()
    )

    tiempos["inicializacion_bd"] = (
        inicializar_base_datos()
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

    tiempos["cdc_bronze"] = (
        ingesta_cdc()
    )

    tiempos["validacion_bronze"] = (
        validar_conteos_bronze()
    )

    tiempos["staging"] = (
        cargar_staging()
    )

    tiempos["procesar_cdc"] = (
        procesar_cdc()
    )

    tiempos["catalogos_usuarios"] = (
        construir_catalogos_usuarios()
    )

    tiempos["dbt_run"] = (
        ejecutar_dbt()
    )

    tiempos["dbt_test"] = (
        ejecutar_tests()
    )

    snapshot = guardar_snapshot(
        tiempos
    )

    vaciar_staging()

    duracion_total = round(
        time.perf_counter()
        - inicio_total,
        2,
    )

    tiempos["total"] = (
        duracion_total
    )

    print()
    print("=" * 80)
    print(
        "PROYECTO 2 - FASE 1.1 COMPLETADA"
    )
    print("=" * 80)

    for etapa, segundos in tiempos.items():

        print(
            f"{etapa:<25}: "
            f"{segundos:>12.2f} s"
        )

    print("-" * 80)

    print(
        f"Snapshot: {snapshot}"
    )

    print("=" * 80)

    logger.info(
        "Fase 1.1 finalizada correctamente."
    )


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Pipeline Proyecto 2 "
            "- Red Metropolitana"
        )
    )

    parser.add_argument(
        "--desde-cero",
        action="store_true",
        help=(
            "Elimina el estado generado de P2 "
            "y reconstruye todo."
        ),
    )

    parser.add_argument(
        "--solo-validar",
        action="store_true",
        help=(
            "Valida configuración y archivos "
            "sin ejecutar el pipeline."
        ),
    )
    
    parser.add_argument(
        "--reanudar-desde-aerometro",
        action="store_true",
        help=(
            "Reanuda una corrida fallida "
            "desde Aerómetro y continúa "
            "hasta finalizar Fase 1.1."
        ),
    )
    
    parser.add_argument(
        "--reanudar-desde-dbt",
        action="store_true",
        help=(
            "Reanuda una corrida de Fase 1.1 "
            "desde dbt sin repetir la ingesta."
        ),
    )
    

    args = parser.parse_args()

    flujo_proyecto2(
        desde_cero=args.desde_cero,
        solo_validar=args.solo_validar,
        reanudar_desde_aerometro=(
            args.reanudar_desde_aerometro
        ),
        reanudar_desde_dbt=(
            args.reanudar_desde_dbt
        ),
    )