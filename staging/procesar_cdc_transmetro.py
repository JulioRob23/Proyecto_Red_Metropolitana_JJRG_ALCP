from pathlib import Path
import glob
import os
import re

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


# --------------------------------------------------
# Configuración
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

BRONZE_PATTERN = str(
    PROJECT_ROOT
    / "lake"
    / "bronze"
    / "cdc_padron"
    / "ingestion_date=*"
    / "*.parquet"
)

METRICS_DIR = (
    PROJECT_ROOT
    / "docs"
    / "metricas"
)

METRICS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def conectar_postgres():

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        dbname=os.getenv(
            "POSTGRES_DB",
            "red_metropolitana"
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "red_user"
        ),
        password=os.getenv("POSTGRES_PASSWORD")
    )


def clasificar_llave(tarjeta):

    tarjeta = str(tarjeta)

    if re.fullmatch(r"TC-\d{8}", tarjeta):
        return "TRANSMETRO"

    if re.fullmatch(r"\d{10}", tarjeta):
        return "TRANSURBANO"

    if re.fullmatch(r"MR\d{7}", tarjeta):
        return "METRORIEL"

    if tarjeta == "SIN-TARJETA":
        return "SIN_TARJETA"

    return "OTRA"


def leer_bronze():

    archivos = glob.glob(BRONZE_PATTERN)

    if not archivos:
        raise FileNotFoundError(
            "No se encontraron archivos CDC en Bronze."
        )

    dfs = [
        pd.read_parquet(archivo)
        for archivo in archivos
    ]

    df = pd.concat(
        dfs,
        ignore_index=True
    )

    # Evita duplicar el mismo evento si el mismo
    # archivo Bronze estuviera presente más de una vez.
    df = df.drop_duplicates(
        subset=[
            "_source_sha256",
            "seq"
        ]
    )

    df["seq"] = pd.to_numeric(
        df["seq"]
    ).astype("int64")

    df["tipo_llave"] = (
        df["tarjeta"]
        .apply(clasificar_llave)
    )

    return df.sort_values("seq")


def cargar_staging(conn, df):

    columnas = [
        "seq",
        "commit_ts",
        "op",
        "tarjeta",
        "perfil",
        "zona_residencia",
        "estado",
        "tipo_llave",
        "_ingested_at",
        "_source_file",
        "_source_sha256"
    ]

    datos = (
        df[columnas]
        .where(pd.notna(df[columnas]), None)
    )

    valores = list(
        datos.itertuples(
            index=False,
            name=None
        )
    )

    with conn.cursor() as cursor:

        cursor.execute(
            "TRUNCATE TABLE staging.cdc_padron_eventos;"
        )

        execute_values(
            cursor,
            """
            INSERT INTO staging.cdc_padron_eventos (
                seq,
                commit_ts,
                op,
                tarjeta,
                perfil,
                zona_residencia,
                estado,
                tipo_llave,
                _ingested_at,
                _source_file,
                _source_sha256
            )
            VALUES %s
            """,
            valores,
            page_size=5000
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM staging.cdc_padron_eventos;
            """
        )

        filas_staging = cursor.fetchone()[0]

    return filas_staging


def construir_padron_transmetro(df):

    # Únicamente llaves de Transmetro.
    tm = (
        df[
            df["tipo_llave"]
            == "TRANSMETRO"
        ]
        .copy()
        .sort_values("seq")
    )

    # Si no respetáramos los DELETE, todas las
    # tarjetas observadas permanecerían activas.
    tarjetas_antes_borrados = (
        tm["tarjeta"].nunique()
    )

    estado_actual = {}

    # --------------------------------------------------
    # Aplicar eventos EN ORDEN DE SECUENCIA
    # --------------------------------------------------

    for fila in tm.itertuples(index=False):

        tarjeta = fila.tarjeta
        operacion = fila.op

        if operacion in (
            "INSERT",
            "UPDATE"
        ):

            estado_actual[tarjeta] = {
                "tarjeta": tarjeta,
                "perfil": (
                    fila.perfil
                    if fila.perfil != ""
                    else None
                ),
                "zona_residencia": (
                    fila.zona_residencia
                    if fila.zona_residencia != ""
                    else None
                ),
                "estado": (
                    fila.estado
                    if fila.estado != ""
                    else "ACTIVA"
                ),
                "activo": True,
                "ultima_seq": int(fila.seq),
                "ultima_op": operacion,
                "ultimo_commit_ts": fila.commit_ts
            }

        elif operacion == "DELETE":

            # Si ya conocemos la tarjeta, conservamos
            # sus últimos atributos conocidos.
            if tarjeta in estado_actual:

                registro = estado_actual[tarjeta]

                registro["estado"] = "INACTIVA"
                registro["activo"] = False
                registro["ultima_seq"] = int(fila.seq)
                registro["ultima_op"] = "DELETE"
                registro["ultimo_commit_ts"] = (
                    fila.commit_ts
                )

            # Si solamente conocemos la tarjeta porque
            # llegó un tombstone, NO inventamos atributos.
            else:

                estado_actual[tarjeta] = {
                    "tarjeta": tarjeta,
                    "perfil": None,
                    "zona_residencia": None,
                    "estado": "INACTIVA",
                    "activo": False,
                    "ultima_seq": int(fila.seq),
                    "ultima_op": "DELETE",
                    "ultimo_commit_ts": fila.commit_ts
                }

    padron = pd.DataFrame(
        estado_actual.values()
    )

    activos = int(
        padron["activo"].sum()
    )

    inactivos = int(
        (~padron["activo"]).sum()
    )

    return (
        tm,
        padron,
        tarjetas_antes_borrados,
        activos,
        inactivos
    )


def guardar_padron(conn, padron):

    columnas = [
        "tarjeta",
        "perfil",
        "zona_residencia",
        "estado",
        "activo",
        "ultima_seq",
        "ultima_op",
        "ultimo_commit_ts"
    ]

    datos = (
        padron[columnas]
        .where(pd.notna(padron[columnas]), None)
    )

    valores = list(
        datos.itertuples(
            index=False,
            name=None
        )
    )

    with conn.cursor() as cursor:

        cursor.execute(
            """
            TRUNCATE TABLE
            cdc.padron_transmetro_vigente;
            """
        )

        execute_values(
            cursor,
            """
            INSERT INTO cdc.padron_transmetro_vigente (
                tarjeta,
                perfil,
                zona_residencia,
                estado,
                activo,
                ultima_seq,
                ultima_op,
                ultimo_commit_ts
            )
            VALUES %s
            """,
            valores,
            page_size=5000
        )


def vaciar_staging(conn):

    with conn.cursor() as cursor:

        cursor.execute(
            """
            TRUNCATE TABLE
            staging.cdc_padron_eventos;
            """
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM staging.cdc_padron_eventos;
            """
        )

        return cursor.fetchone()[0]


def main():

    print("=" * 72)
    print("FASE 1.2 - STAGING Y CDC DE TRANSMETRO")
    print("=" * 72)

    df = leer_bronze()

    print(
        f"Eventos CDC leídos desde Bronze: "
        f"{len(df)}"
    )

    print()
    print("Operaciones CDC totales:")

    for operacion, cantidad in (
        df["op"]
        .value_counts()
        .sort_index()
        .items()
    ):
        print(
            f"  {operacion:<8}: {cantidad}"
        )

    print()
    print("Eventos por tipo de llave:")

    conteo_llaves = (
        df["tipo_llave"]
        .value_counts()
    )

    for tipo, cantidad in conteo_llaves.items():
        print(
            f"  {tipo:<12}: {cantidad}"
        )

    conn = conectar_postgres()

    try:

        filas_staging = cargar_staging(
            conn,
            df
        )

        print()
        print(
            f"[OK] Eventos cargados a Staging: "
            f"{filas_staging}"
        )

        (
            tm,
            padron,
            antes_borrados,
            activos,
            inactivos
        ) = construir_padron_transmetro(df)

        guardar_padron(
            conn,
            padron
        )

        print()
        print("CDC específico de Transmetro:")

        conteo_ops_tm = (
            tm["op"]
            .value_counts()
            .to_dict()
        )

        print(
            f"  INSERT : "
            f"{conteo_ops_tm.get('INSERT', 0)}"
        )

        print(
            f"  UPDATE : "
            f"{conteo_ops_tm.get('UPDATE', 0)}"
        )

        print(
            f"  DELETE : "
            f"{conteo_ops_tm.get('DELETE', 0)}"
        )

        print()
        print(
            f"Tarjetas antes de aplicar bajas: "
            f"{antes_borrados}"
        )

        print(
            f"Tarjetas activas finales: "
            f"{activos}"
        )

        print(
            f"Tarjetas inactivas finales: "
            f"{inactivos}"
        )

        print(
            f"Total padrón vigente: "
            f"{len(padron)}"
        )

        # ----------------------------------------------
        # Métricas para documentación
        # ----------------------------------------------

        metricas = pd.DataFrame([
            {
                "metrica": "Eventos CDC totales",
                "valor": len(df)
            },
            {
                "metrica": "Eventos CDC Transmetro",
                "valor": len(tm)
            },
            {
                "metrica": "Tarjetas antes de aplicar bajas",
                "valor": antes_borrados
            },
            {
                "metrica": "Tarjetas activas finales",
                "valor": activos
            },
            {
                "metrica": "Tarjetas inactivas finales",
                "valor": inactivos
            },
            {
                "metrica": "Total padrón Transmetro",
                "valor": len(padron)
            }
        ])

        metricas.to_csv(
            METRICS_DIR
            / "cdc_transmetro_fase1_2.csv",
            index=False,
            encoding="utf-8-sig"
        )

        with open(
            METRICS_DIR
            / "cdc_transmetro_fase1_2.md",
            "w",
            encoding="utf-8"
        ) as archivo:

            archivo.write(
                "# Métricas CDC Transmetro - Fase 1.2\n\n"
            )

            archivo.write(
                metricas.to_markdown(index=False)
            )

            archivo.write("\n")

        # ----------------------------------------------
        # Staging debe quedar vacío
        # ----------------------------------------------

        staging_final = vaciar_staging(
            conn
        )

        conn.commit()

        print()
        print(
            f"[OK] Staging al finalizar: "
            f"{staging_final} filas"
        )

        print(
            "[OK] Padrón vigente guardado en "
            "cdc.padron_transmetro_vigente"
        )

        print("=" * 72)

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()