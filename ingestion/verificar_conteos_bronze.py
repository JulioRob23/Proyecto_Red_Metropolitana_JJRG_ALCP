from pathlib import Path
import glob

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "datos" / "raw"
BRONZE_DIR = PROJECT_ROOT / "lake" / "bronze"

OUTPUT_DIR = PROJECT_ROOT / "docs" / "metricas"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


FUENTES = [
    {
        "archivo": "tm_estaciones.csv",
        "bronze": "tm_estaciones",
        "tipo": "csv",
        "via": "Batch"
    },
    {
        "archivo": "tu_paradas.csv",
        "bronze": "tu_paradas",
        "tipo": "csv",
        "via": "Batch"
    },
    {
        "archivo": "mr_estaciones.csv",
        "bronze": "mr_estaciones",
        "tipo": "csv",
        "via": "Batch"
    },
    {
        "archivo": "am_estaciones.csv",
        "bronze": "am_estaciones",
        "tipo": "csv",
        "via": "Batch"
    },
    {
        "archivo": "transmetro_validaciones.csv",
        "bronze": "transmetro",
        "tipo": "csv",
        "via": "Streaming"
    },
    {
        "archivo": "transurbano_transacciones.csv",
        "bronze": "transurbano",
        "tipo": "csv",
        "via": "Streaming"
    },
    {
        "archivo": "metroriel_viajes.jsonl",
        "bronze": "metroriel",
        "tipo": "jsonl",
        "via": "Batch"
    },
    {
        "archivo": "aerometro_boardings.csv",
        "bronze": "aerometro",
        "tipo": "csv",
        "via": "Streaming"
    },
    {
        "archivo": "cdc_padron_usuarios.csv",
        "bronze": "cdc_padron",
        "tipo": "csv",
        "via": "CDC"
    },
]


def contar_origen(archivo, tipo):

    ruta = RAW_DIR / archivo

    if tipo == "csv":

        df = pd.read_csv(
            ruta,
            dtype=str,
            keep_default_na=False
        )

        return len(df)

    if tipo == "jsonl":

        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as f:

            return sum(
                1
                for linea in f
                if linea.strip()
            )

    raise ValueError(
        f"Tipo no soportado: {tipo}"
    )


def contar_bronze(carpeta):

    patron = str(
        BRONZE_DIR
        / carpeta
        / "ingestion_date=*"
        / "*.parquet"
    )

    archivos = glob.glob(patron)

    filas = sum(
        pq.ParquetFile(archivo).metadata.num_rows
        for archivo in archivos
    )

    return filas, len(archivos)


def main():

    resultados = []

    print("=" * 100)
    print("VERIFICACIÓN DE CONTEOS - FASE 1.1")
    print("=" * 100)

    for fuente in FUENTES:

        origen = contar_origen(
            fuente["archivo"],
            fuente["tipo"]
        )

        bronze, parquet = contar_bronze(
            fuente["bronze"]
        )

        estado = (
            "OK"
            if origen == bronze
            else "ERROR"
        )

        resultados.append({
            "archivo": fuente["archivo"],
            "via_ingesta": fuente["via"],
            "filas_origen": origen,
            "filas_bronze": bronze,
            "archivos_parquet": parquet,
            "estado": estado
        })

    df = pd.DataFrame(resultados)

    print(
        df.to_string(
            index=False
        )
    )

    print()
    print("-" * 100)

    print(
        f"Total origen: "
        f"{df['filas_origen'].sum()}"
    )

    print(
        f"Total Bronze: "
        f"{df['filas_bronze'].sum()}"
    )

    errores = (
        df["estado"] != "OK"
    ).sum()

    print(
        f"Fuentes con error: {errores}"
    )

    print("=" * 100)

    # --------------------------------------------------
    # Guardar entregable
    # --------------------------------------------------

    ruta_csv = (
        OUTPUT_DIR
        / "conteos_fase1_1.csv"
    )

    df.to_csv(
        ruta_csv,
        index=False,
        encoding="utf-8-sig"
    )

    ruta_md = (
        OUTPUT_DIR
        / "conteos_fase1_1.md"
    )

    with open(
        ruta_md,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "# Conteos de ingesta - Fase 1.1\n\n"
        )

        archivo.write(
            df.to_markdown(index=False)
        )

        archivo.write("\n")

    print()
    print(
        "[OK] Tabla guardada en:"
    )

    print(
        ruta_csv.relative_to(
            PROJECT_ROOT
        )
    )

    print(
        ruta_md.relative_to(
            PROJECT_ROOT
        )
    )


if __name__ == "__main__":
    main()