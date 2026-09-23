from pathlib import Path
from datetime import datetime
import hashlib

import pandas as pd


# --------------------------------------------------
# Rutas
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_FILE = "cdc_padron_usuarios.csv"

SOURCE_PATH = (
    PROJECT_ROOT
    / "datos"
    / "raw"
    / SOURCE_FILE
)

BRONZE_DIR = (
    PROJECT_ROOT
    / "lake"
    / "bronze"
    / "cdc_padron"
)


def calcular_sha256(ruta_archivo):
    """Calcula SHA-256 del archivo fuente."""

    sha256 = hashlib.sha256()

    with open(ruta_archivo, "rb") as archivo:
        for bloque in iter(
            lambda: archivo.read(1024 * 1024),
            b""
        ):
            sha256.update(bloque)

    return sha256.hexdigest()


def main():

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró: {SOURCE_PATH}"
        )

    print("=" * 70)
    print("INGESTA CDC -> BRONZE")
    print("=" * 70)

    # --------------------------------------------------
    # Leer todo como texto.
    # No se aplican INSERT / UPDATE / DELETE todavía.
    # --------------------------------------------------

    df = pd.read_csv(
        SOURCE_PATH,
        dtype=str,
        keep_default_na=False
    )

    filas_origen = len(df)

    # --------------------------------------------------
    # Metadatos técnicos
    # --------------------------------------------------

    fecha_hora_ingesta = datetime.now().astimezone()
    fecha_ingesta = fecha_hora_ingesta.date().isoformat()

    hash_archivo = calcular_sha256(SOURCE_PATH)

    df["_ingested_at"] = fecha_hora_ingesta.isoformat()
    df["_source_file"] = SOURCE_FILE
    df["_source_sha256"] = hash_archivo

    # --------------------------------------------------
    # Partición
    # --------------------------------------------------

    directorio_destino = (
        BRONZE_DIR
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
    # Guardar Bronze
    # --------------------------------------------------

    df.to_parquet(
        ruta_destino,
        index=False,
        engine="pyarrow"
    )

    print(f"Archivo: {SOURCE_FILE}")
    print(f"Filas origen: {filas_origen}")
    print(
        f"Destino: "
        f"{ruta_destino.relative_to(PROJECT_ROOT)}"
    )
    print(f"SHA-256: {hash_archivo}")

    print()
    print("=" * 70)
    print(
        f"[OK] Filas cargadas en Bronze: "
        f"{filas_origen}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()