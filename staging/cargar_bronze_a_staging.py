from pathlib import Path
from io import StringIO
import glob
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# --------------------------------------------------
# Configuración
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

BRONZE_DIR = (
    PROJECT_ROOT
    / "lake"
    / "bronze"
)


FUENTES = [
    {
        "nombre": "Catálogo Transmetro",
        "carpeta": "tm_estaciones",
        "tabla": "staging.tm_estaciones_raw",
        "columnas": [
            "estacion_id",
            "nombre",
            "linea",
            "zona",
            "lat",
            "lon",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Catálogo Transurbano",
        "carpeta": "tu_paradas",
        "tabla": "staging.tu_paradas_raw",
        "columnas": [
            "cod_parada",
            "descripcion",
            "ruta",
            "sector",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Catálogo MetroRiel",
        "carpeta": "mr_estaciones",
        "tabla": "staging.mr_estaciones_raw",
        "columnas": [
            "id_estacion",
            "nombre_estacion",
            "zona_nombre",
            "km",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Catálogo Aerómetro",
        "carpeta": "am_estaciones",
        "tabla": "staging.am_estaciones_raw",
        "columnas": [
            "station_code",
            "station_name",
            "axis",
            "district",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Transmetro",
        "carpeta": "transmetro",
        "tabla": "staging.transmetro_validaciones_raw",
        "columnas": [
            "validacion_id",
            "tarjeta",
            "estacion_id",
            "linea",
            "fecha_hora",
            "tarifa",
            "tipo",
            "_row_number",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Transurbano",
        "carpeta": "transurbano",
        "tabla": "staging.transurbano_transacciones_raw",
        "columnas": [
            "fecha",
            "hora",
            "num_tarjeta",
            "cod_parada",
            "ruta",
            "monto_centavos",
            "cod_estado",
            "_row_number",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "MetroRiel",
        "carpeta": "metroriel",
        "tabla": "staging.metroriel_viajes_raw",
        "columnas": [
            "_line_number",
            "raw_json",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "Aerómetro",
        "carpeta": "aerometro",
        "tabla": "staging.aerometro_boardings_raw",
        "columnas": [
            "boarding_id",
            "user_hash",
            "station_code",
            "axis",
            "timestamp_utc",
            "cabin_number",
            "fare",
            "_row_number",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    },
    {
        "nombre": "CDC padrón",
        "carpeta": "cdc_padron",
        "tabla": "staging.cdc_padron_raw",
        "columnas": [
            "seq",
            "commit_ts",
            "op",
            "tarjeta",
            "perfil",
            "zona_residencia",
            "estado",
            "_ingested_at",
            "_source_file",
            "_source_sha256"
        ]
    }
]


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


def obtener_archivos(carpeta):

    patron = str(
        BRONZE_DIR
        / carpeta
        / "ingestion_date=*"
        / "*.parquet"
    )

    return sorted(
        glob.glob(patron)
    )


def copiar_dataframe(
    cursor,
    tabla,
    columnas,
    df
):

    buffer = StringIO()

    df.to_csv(
        buffer,
        index=False,
        columns=columnas,
        header=True,
        na_rep=""
    )

    buffer.seek(0)

    lista_columnas = ", ".join(
        columnas
    )

    sql = f"""
        COPY {tabla} (
            {lista_columnas}
        )
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER TRUE,
            ENCODING 'UTF8'
        )
    """

    cursor.copy_expert(
        sql,
        buffer
    )


def cargar_fuente(
    conn,
    fuente
):

    archivos = obtener_archivos(
        fuente["carpeta"]
    )

    if not archivos:
        raise FileNotFoundError(
            f"No se encontró Bronze para "
            f"{fuente['nombre']}"
        )

    with conn.cursor() as cursor:

        # La carga debe ser idempotente.
        cursor.execute(
            f"TRUNCATE TABLE "
            f"{fuente['tabla']};"
        )

        for archivo in archivos:

            df = pd.read_parquet(
                archivo,
                columns=fuente["columnas"]
            )

            copiar_dataframe(
                cursor,
                fuente["tabla"],
                fuente["columnas"],
                df
            )

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {fuente['tabla']};
            """
        )

        total = cursor.fetchone()[0]

    return total


def main():

    print("=" * 82)
    print("FASE 1.3 - CARGA BRONZE -> STAGING")
    print("=" * 82)

    conn = conectar_postgres()

    resultados = []

    try:

        for fuente in FUENTES:

            print()
            print(
                f"Cargando "
                f"{fuente['nombre']}..."
            )

            total = cargar_fuente(
                conn,
                fuente
            )

            conn.commit()

            resultados.append(
                (
                    fuente["nombre"],
                    total
                )
            )

            print(
                f"[OK] {fuente['nombre']}: "
                f"{total} filas"
            )

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

    print()
    print("=" * 82)
    print("RESUMEN DE STAGING")
    print("=" * 82)

    total_general = 0

    for nombre, total in resultados:

        print(
            f"{nombre:<25} "
            f"{total:>10}"
        )

        total_general += total

    print("-" * 82)

    print(
        f"{'TOTAL':<25} "
        f"{total_general:>10}"
    )

    print("=" * 82)


if __name__ == "__main__":
    main()