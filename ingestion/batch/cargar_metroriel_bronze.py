from pathlib import Path
from datetime import datetime
import hashlib

import pandas as pd


# --------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "datos" / "raw"
BRONZE_DIR = PROJECT_ROOT / "lake" / "bronze"


SOURCE_FILE = "metroriel_viajes.jsonl"
SOURCE_NAME = "metroriel"


def calcular_sha256(ruta_archivo):
    """Calcula el hash SHA-256 del archivo."""

    sha256 = hashlib.sha256()

    with open(ruta_archivo, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()


def cargar_metroriel():
    """Carga el JSON Lines de MetroRiel a Bronze."""

    ruta_origen = RAW_DIR / SOURCE_FILE

    if not ruta_origen.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta_origen}"
        )

    print("=" * 70)
    print("CARGA BATCH DE METRORIEL A BRONZE")
    print("=" * 70)

    # --------------------------------------------------
    # Leer cada línea sin transformar el JSON
    # --------------------------------------------------

    registros = []

    with open(ruta_origen, "r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):

            linea = linea.rstrip("\r\n")

            if not linea:
                continue

            registros.append({
                "_line_number": numero_linea,
                "raw_json": linea
            })

    df = pd.DataFrame(registros)

    filas_origen = len(df)

    # --------------------------------------------------
    # Metadatos técnicos
    # --------------------------------------------------

    fecha_hora_ingesta = datetime.now().astimezone()
    fecha_ingesta = fecha_hora_ingesta.date().isoformat()

    hash_archivo = calcular_sha256(ruta_origen)

    df["_ingested_at"] = fecha_hora_ingesta.isoformat()
    df["_source_file"] = SOURCE_FILE
    df["_source_sha256"] = hash_archivo

    # --------------------------------------------------
    # Crear partición Bronze
    # --------------------------------------------------

    directorio_destino = (
        BRONZE_DIR
        / SOURCE_NAME
        / f"ingestion_date={fecha_ingesta}"
    )

    directorio_destino.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_destino = (
        directorio_destino
        / f"part-{hash_archivo[:12]}.parquet"
    )

    # --------------------------------------------------
    # Guardar en Parquet
    # --------------------------------------------------

    df.to_parquet(
        ruta_destino,
        index=False,
        engine="pyarrow"
    )

    print(
        f"[OK] {SOURCE_FILE}"
    )

    print(
        f"     Filas cargadas: {filas_origen}"
    )

    print(
        f"     Destino: "
        f"{ruta_destino.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"     SHA-256: {hash_archivo}"
    )

    print("=" * 70)

    return filas_origen


if __name__ == "__main__":
    cargar_metroriel()