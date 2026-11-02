from pathlib import Path
import glob
import json
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
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


# --------------------------------------------------
# Transurbano
# --------------------------------------------------

def extraer_transurbano():

    patron = str(
        BRONZE_DIR
        / "transurbano"
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(patron)

    if not archivos:
        raise FileNotFoundError(
            "No se encontró Bronze de Transurbano."
        )

    valores = set()

    for archivo in archivos:

        df = pd.read_parquet(
            archivo,
            columns=["num_tarjeta"]
        )

        valores.update(
            valor
            for valor in df["num_tarjeta"]
            if pd.notna(valor)
            and str(valor).strip() != ""
        )

    return sorted(valores)


# --------------------------------------------------
# MetroRiel
# --------------------------------------------------

def extraer_metroriel():

    patron = str(
        BRONZE_DIR
        / "metroriel"
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(patron)

    if not archivos:
        raise FileNotFoundError(
            "No se encontró Bronze de MetroRiel."
        )

    valores = set()

    for archivo in archivos:

        df = pd.read_parquet(
            archivo,
            columns=["raw_json"]
        )

        for raw_json in df["raw_json"]:

            registro = json.loads(
                raw_json
            )

            tarjeta = registro.get(
                "card"
            )

            if (
                tarjeta is not None
                and str(tarjeta).strip() != ""
            ):
                valores.add(
                    str(tarjeta)
                )

    return sorted(valores)


# --------------------------------------------------
# Aerómetro
# --------------------------------------------------

def extraer_aerometro():

    patron = str(
        BRONZE_DIR
        / "aerometro"
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(patron)

    if not archivos:
        raise FileNotFoundError(
            "No se encontró Bronze de Aerómetro."
        )

    valores = set()

    for archivo in archivos:

        df = pd.read_parquet(
            archivo,
            columns=["user_hash"]
        )

        valores.update(
            valor
            for valor in df["user_hash"]
            if pd.notna(valor)
            and str(valor).strip() != ""
        )

    return sorted(valores)


def cargar_catalogo(
    conn,
    tabla,
    columna,
    valores
):

    with conn.cursor() as cursor:

        cursor.execute(
            f"TRUNCATE TABLE {tabla};"
        )

        execute_values(
            cursor,
            f"""
            INSERT INTO {tabla} (
                {columna}
            )
            VALUES %s
            """,
            [
                (valor,)
                for valor in valores
            ],
            page_size=5000
        )


def main():

    print("=" * 72)
    print("FASE 1.2B - CATÁLOGOS MÍNIMOS DE USUARIOS")
    print("=" * 72)

    # --------------------------------------------------
    # Extraer llaves únicas desde Bronze
    # --------------------------------------------------

    print()
    print("Extrayendo usuarios de Transurbano...")

    usuarios_tu = extraer_transurbano()

    print(
        f"[OK] Usuarios únicos Transurbano: "
        f"{len(usuarios_tu)}"
    )

    print()
    print("Extrayendo usuarios de MetroRiel...")

    usuarios_mr = extraer_metroriel()

    print(
        f"[OK] Usuarios únicos MetroRiel: "
        f"{len(usuarios_mr)}"
    )

    print()
    print("Extrayendo usuarios de Aerómetro...")

    usuarios_am = extraer_aerometro()

    print(
        f"[OK] Usuarios únicos Aerómetro: "
        f"{len(usuarios_am)}"
    )

    # --------------------------------------------------
    # Guardar en PostgreSQL
    # --------------------------------------------------

    conn = conectar_postgres()

    try:

        cargar_catalogo(
            conn,
            "catalogos.usuarios_transurbano",
            "num_tarjeta",
            usuarios_tu
        )

        cargar_catalogo(
            conn,
            "catalogos.usuarios_metroriel",
            "card",
            usuarios_mr
        )

        cargar_catalogo(
            conn,
            "catalogos.usuarios_aerometro",
            "user_hash",
            usuarios_am
        )

        conn.commit()

        print()
        print(
            "[OK] Catálogos guardados "
            "correctamente en PostgreSQL."
        )

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

    # --------------------------------------------------
    # Métricas
    # --------------------------------------------------

    metricas = pd.DataFrame([
        {
            "operador": "Transurbano",
            "campo_llave": "num_tarjeta",
            "usuarios_unicos": len(
                usuarios_tu
            )
        },
        {
            "operador": "MetroRiel",
            "campo_llave": "card",
            "usuarios_unicos": len(
                usuarios_mr
            )
        },
        {
            "operador": "Aerómetro",
            "campo_llave": "user_hash",
            "usuarios_unicos": len(
                usuarios_am
            )
        }
    ])

    ruta_csv = (
        METRICS_DIR
        / "catalogos_usuarios_fase1_2.csv"
    )

    metricas.to_csv(
        ruta_csv,
        index=False,
        encoding="utf-8-sig"
    )

    ruta_md = (
        METRICS_DIR
        / "catalogos_usuarios_fase1_2.md"
    )

    with open(
        ruta_md,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "# Catálogos mínimos de usuarios - Fase 1.2\n\n"
        )

        archivo.write(
            metricas.to_markdown(
                index=False
            )
        )

        archivo.write("\n")

    print()
    print("=" * 72)

    print(
        f"Transurbano : "
        f"{len(usuarios_tu)}"
    )

    print(
        f"MetroRiel   : "
        f"{len(usuarios_mr)}"
    )

    print(
        f"Aerómetro   : "
        f"{len(usuarios_am)}"
    )

    print("=" * 72)

    print()
    print(
        "[OK] Métricas guardadas en "
        "docs/metricas/"
    )


if __name__ == "__main__":
    main()