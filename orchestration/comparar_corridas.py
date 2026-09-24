from pathlib import Path
import json
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CORRIDAS_DIR = (
    PROJECT_ROOT
    / "docs"
    / "metricas"
    / "corridas"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "metricas"
)


def cargar_json(ruta):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


def agregar_capa(
    resultados,
    capa,
    corrida_1,
    corrida_2
):

    claves = sorted(
        set(corrida_1.keys())
        | set(corrida_2.keys())
    )

    for clave in claves:

        valor_1 = corrida_1.get(clave)
        valor_2 = corrida_2.get(clave)

        resultados.append({
            "capa": capa,
            "objeto": clave,
            "corrida_1": valor_1,
            "corrida_2": valor_2,
            "igual": valor_1 == valor_2
        })


def main():

    archivos = sorted(
        CORRIDAS_DIR.glob(
            "corrida_*.json"
        )
    )

    if len(archivos) < 2:

        print(
            "[ERROR] Se necesitan al menos "
            "dos snapshots."
        )

        sys.exit(1)

    # Utilizamos las dos corridas más recientes.
    ruta_1 = archivos[-2]
    ruta_2 = archivos[-1]

    corrida_1 = cargar_json(
        ruta_1
    )

    corrida_2 = cargar_json(
        ruta_2
    )

    resultados = []

    agregar_capa(
        resultados,
        "Bronze",
        corrida_1["bronze"],
        corrida_2["bronze"]
    )

    agregar_capa(
        resultados,
        "Silver",
        corrida_1["silver"],
        corrida_2["silver"]
    )

    agregar_capa(
        resultados,
        "Gold",
        corrida_1["gold"],
        corrida_2["gold"]
    )

    resultados.append({
        "capa": "Calidad",
        "objeto": "cuarentena",
        "corrida_1": corrida_1[
            "cuarentena"
        ],
        "corrida_2": corrida_2[
            "cuarentena"
        ],
        "igual": (
            corrida_1["cuarentena"]
            == corrida_2["cuarentena"]
        )
    })

    df = pd.DataFrame(
        resultados
    )

    errores = (
        ~df["igual"]
    ).sum()

    print("=" * 90)
    print("COMPARACIÓN DE IDEMPOTENCIA - FASE 1")
    print("=" * 90)

    print()
    print(
        f"Corrida 1: {ruta_1.name}"
    )

    print(
        f"Corrida 2: {ruta_2.name}"
    )

    print()

    print(
        df.to_string(
            index=False
        )
    )

    print()
    print("-" * 90)

    if errores == 0:

        print(
            "[OK] IDEMPOTENCIA VERIFICADA"
        )

        print(
            "Los conteos de Bronze, "
            "Silver y Gold no cambiaron."
        )

    else:

        print(
            f"[ERROR] Se detectaron "
            f"{errores} diferencias."
        )

    print("=" * 90)

    # ----------------------------------------------
    # Guardar entregables
    # ----------------------------------------------

    ruta_csv = (
        OUTPUT_DIR
        / "idempotencia_fase1.csv"
    )

    df.to_csv(
        ruta_csv,
        index=False,
        encoding="utf-8-sig"
    )

    ruta_md = (
        OUTPUT_DIR
        / "idempotencia_fase1.md"
    )

    with open(
        ruta_md,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "# Verificación de idempotencia - Fase 1\n\n"
        )

        archivo.write(
            f"**Corrida 1:** `{ruta_1.name}`\n\n"
        )

        archivo.write(
            f"**Corrida 2:** `{ruta_2.name}`\n\n"
        )

        archivo.write(
            df.to_markdown(
                index=False
            )
        )

        archivo.write("\n\n")

        if errores == 0:

            archivo.write(
                "**Resultado:** Idempotencia "
                "verificada. Los conteos no "
                "cambiaron entre corridas.\n"
            )

        else:

            archivo.write(
                f"**Resultado:** Se detectaron "
                f"{errores} diferencias entre "
                f"las corridas.\n"
            )

    print()
    print(
        "[OK] Evidencias guardadas:"
    )

    print(
        "docs/metricas/"
        "idempotencia_fase1.csv"
    )

    print(
        "docs/metricas/"
        "idempotencia_fase1.md"
    )

    if errores != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()