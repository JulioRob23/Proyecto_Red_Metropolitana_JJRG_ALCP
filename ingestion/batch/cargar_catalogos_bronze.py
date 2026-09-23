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


# --------------------------------------------------
# Catálogos que ingresan por Batch
# --------------------------------------------------

CATALOGOS = {
    "tm_estaciones.csv": "tm_estaciones",
    "tu_paradas.csv": "tu_paradas",
    "mr_estaciones.csv": "mr_estaciones",
    "am_estaciones.csv": "am_estaciones",
}


def calcular_sha256(ruta_archivo):
    """Calcula el hash SHA-256 de un archivo."""

    sha256 = hashlib.sha256()

    with open(ruta_archivo, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()


def cargar_catalogo(nombre_archivo, nombre_fuente):
    """Carga un catálogo CSV a Bronze sin transformar sus datos."""

    ruta_origen = RAW_DIR / nombre_archivo

    if not ruta_origen.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta_origen}"
        )

    # Leer todas las columnas como texto para evitar
    # transformaciones automáticas en Bronze.
    df = pd.read_csv(
        ruta_origen,
        dtype=str,
        keep_default_na=False
    )

    filas_origen = len(df)

    # --------------------------------------------------
    # Metadatos de ingesta
    # --------------------------------------------------

    fecha_hora_ingesta = datetime.now().astimezone()
    fecha_ingesta = fecha_hora_ingesta.date().isoformat()

    hash_archivo = calcular_sha256(ruta_origen)

    df["_ingested_at"] = fecha_hora_ingesta.isoformat()
    df["_source_file"] = nombre_archivo
    df["_source_sha256"] = hash_archivo

    # --------------------------------------------------
    # Partición Bronze
    # --------------------------------------------------

    directorio_destino = (
        BRONZE_DIR
        / nombre_fuente
        / f"ingestion_date={fecha_ingesta}"
    )

    directorio_destino.mkdir(
        parents=True,
        exist_ok=True
    )

    # El hash permite utilizar un nombre determinístico.
    # Si se procesa exactamente el mismo archivo otra vez,
    # se sobrescribe la misma salida y no se duplica.
    ruta_destino = (
        directorio_destino
        / f"part-{hash_archivo[:12]}.parquet"
    )

    df.to_parquet(
        ruta_destino,
        index=False,
        engine="pyarrow"
    )

    print(
        f"[OK] {nombre_archivo:<25} "
        f"{filas_origen:>6} filas -> "
        f"{ruta_destino.relative_to(PROJECT_ROOT)}"
    )

    return {
        "archivo": nombre_archivo,
        "fuente": nombre_fuente,
        "filas": filas_origen,
        "hash": hash_archivo,
        "destino": str(ruta_destino),
    }


def main():

    print("=" * 70)
    print("CARGA BATCH DE CATÁLOGOS A BRONZE")
    print("=" * 70)

    resultados = []

    for archivo, fuente in CATALOGOS.items():
        resultado = cargar_catalogo(
            archivo,
            fuente
        )

        resultados.append(resultado)

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)

    total = 0

    for resultado in resultados:
        print(
            f"{resultado['archivo']}: "
            f"{resultado['filas']} filas"
        )

        total += resultado["filas"]

    print("-" * 70)
    print(f"Total cargado: {total} filas")
    print("=" * 70)


if __name__ == "__main__":
    main()