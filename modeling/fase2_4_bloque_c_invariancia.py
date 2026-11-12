from pathlib import Path
import hashlib

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASELINE = (
    PROJECT_ROOT
    / "predicciones"
    / "predicciones_corte_C_baseline.csv"
)

ACTUAL = (
    PROJECT_ROOT
    / "predicciones"
    / "predicciones_corte_C.csv"
)


def sha256(ruta):

    h = hashlib.sha256()

    with open(ruta, "rb") as archivo:

        for bloque in iter(
            lambda: archivo.read(1024 * 1024),
            b""
        ):
            h.update(bloque)

    return h.hexdigest()


def main():

    print()
    print("=" * 72)
    print("PRUEBA DE INVARIANCIA - CORTE C")
    print("=" * 72)

    if not BASELINE.exists():
        raise FileNotFoundError(
            "No existe el baseline del corte C."
        )

    if not ACTUAL.exists():
        raise FileNotFoundError(
            "No existe el archivo actual."
        )

    base = pd.read_csv(BASELINE)

    actual = pd.read_csv(ACTUAL)

    columnas = [
        "unidad_id",
        "tarjetas",
        "puntaje",
        "contactar",
    ]

    if base.columns.tolist() != columnas:
        raise RuntimeError(
            "Columnas inesperadas en baseline."
        )

    if actual.columns.tolist() != columnas:
        raise RuntimeError(
            "Columnas inesperadas en archivo actual."
        )

    base = (
        base
        .sort_values("unidad_id")
        .reset_index(drop=True)
    )

    actual = (
        actual
        .sort_values("unidad_id")
        .reset_index(drop=True)
    )

    mismas_filas = (
        len(base) == len(actual)
    )

    mismas_unidades = (
        base["unidad_id"]
        .equals(
            actual["unidad_id"]
        )
    )

    mismas_tarjetas = (
        base["tarjetas"]
        .equals(
            actual["tarjetas"]
        )
    )

    mismos_contactos = (
        base["contactar"]
        .equals(
            actual["contactar"]
        )
    )

    diferencia_score = float(
        (
            base["puntaje"]
            - actual["puntaje"]
        )
        .abs()
        .max()
    )

    hash_baseline = sha256(BASELINE)
    hash_actual = sha256(ACTUAL)

    print()
    print(f"Filas baseline      : {len(base):,}")
    print(f"Filas actual        : {len(actual):,}")

    print()
    print(f"Mismas filas        : {mismas_filas}")
    print(f"Mismas unidades     : {mismas_unidades}")
    print(f"Mismas tarjetas     : {mismas_tarjetas}")
    print(f"Mismos contactos    : {mismos_contactos}")

    print()
    print(
        "Diferencia máxima score: "
        f"{diferencia_score:.12f}"
    )

    print()
    print(
        f"SHA baseline: {hash_baseline}"
    )

    print(
        f"SHA actual  : {hash_actual}"
    )

    iguales = (
        mismas_filas
        and mismas_unidades
        and mismas_tarjetas
        and mismos_contactos
        and diferencia_score == 0
        and hash_baseline == hash_actual
    )

    print()
    print("=" * 72)

    if iguales:

        print("RESULTADO: INVARIANCIA SUPERADA")

        print(
            "[OK] Las predicciones del corte C "
            "son exactamente idénticas."
        )

    else:

        print("RESULTADO: INVARIANCIA NO SUPERADA")

        raise RuntimeError(
            "Las predicciones cambiaron."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()