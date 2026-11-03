from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

from sklearn.metrics import average_precision_score


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase1"
)

FOLDS_PATH = (
    OUTPUT_DIR
    / "fase1_4_folds.csv"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310
N_FOLDS_ESPERADOS = 5


# ============================================================
# CARGA DEL .ENV
# ============================================================

def cargar_env(ruta):

    valores = {}

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        for linea in archivo:

            linea = linea.strip()

            if (
                not linea
                or linea.startswith("#")
                or "=" not in linea
            ):
                continue

            clave, valor = linea.split(
                "=",
                1
            )

            valores[
                clave.strip()
            ] = (
                valor
                .strip()
                .strip('"')
                .strip("'")
            )

    return valores


# ============================================================
# CONEXIÓN
# ============================================================

def conectar_postgres():

    env = cargar_env(
        ENV_PATH
    )

    return psycopg2.connect(
        dbname=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        host=env["POSTGRES_HOST"],
        port=int(
            env["POSTGRES_PORT"]
        ),
    )


# ============================================================
# CARGAR DATOS DEL CORTE A
# ============================================================

def cargar_datos():

    consulta = """
        SELECT
            unidad_id,
            etiqueta,
            dias_desde_ultimo_viaje
        FROM features.features_usuario
        WHERE corte = 'A'
        ORDER BY unidad_id;
    """

    conexion = conectar_postgres()

    try:

        cursor = conexion.cursor()

        cursor.execute(
            consulta
        )

        filas = cursor.fetchall()

        columnas = [
            descripcion[0]
            for descripcion
            in cursor.description
        ]

        df = pd.DataFrame(
            filas,
            columns=columnas
        )

    finally:
        conexion.close()

    return df


# ============================================================
# UNIR CON FOLDS OFICIALES
# ============================================================

def preparar_datos():

    if not FOLDS_PATH.exists():
        raise FileNotFoundError(
            "No se encontró "
            "fase1_4_folds.csv. "
            "Debe ejecutarse primero "
            "el Bloque A."
        )

    datos = cargar_datos()

    folds = pd.read_csv(
        FOLDS_PATH
    )

    df = datos.merge(
        folds,
        on="unidad_id",
        how="inner",
        suffixes=(
            "_db",
            "_fold"
        ),
        validate="one_to_one",
    )

    if len(df) != FILAS_ESPERADAS:
        raise RuntimeError(
            f"Filas inesperadas: "
            f"{len(df)}"
        )

    if not (
        df["etiqueta_db"].astype(int)
        ==
        df["etiqueta_fold"].astype(int)
    ).all():

        raise RuntimeError(
            "Las etiquetas del archivo "
            "de folds no coinciden con "
            "la tabla de features."
        )

    df["etiqueta"] = (
        df["etiqueta_db"]
        .astype(int)
    )

    if (
        df["etiqueta"].sum()
        != POSITIVOS_ESPERADOS
    ):
        raise RuntimeError(
            "La cantidad de positivos "
            "no coincide con 8,310."
        )

    if (
        df["fold"].nunique()
        != N_FOLDS_ESPERADOS
    ):
        raise RuntimeError(
            "No se encontraron "
            "exactamente 5 folds."
        )

    nulos_recencia = int(
        df[
            "dias_desde_ultimo_viaje"
        ]
        .isna()
        .sum()
    )

    if nulos_recencia != 0:
        raise RuntimeError(
            "dias_desde_ultimo_viaje "
            f"tiene {nulos_recencia} "
            "valores nulos."
        )

    return df


# ============================================================
# BASELINE 1
# PROBABILIDAD CONSTANTE
# ============================================================

def evaluar_baseline_constante(
    df
):

    prevalencia = (
        df["etiqueta"].mean()
    )

    resultados = []

    oof = []

    for fold in sorted(
        df["fold"].unique()
    ):

        validacion = (
            df[
                df["fold"] == fold
            ]
            .copy()
        )

        y_true = (
            validacion[
                "etiqueta"
            ]
            .to_numpy()
        )

        puntajes = np.full(
            len(validacion),
            prevalencia,
            dtype=float,
        )

        ap = average_precision_score(
            y_true,
            puntajes,
        )

        resultados.append({
            "modelo":
                "Baseline prevalencia",
            "fold":
                int(fold),
            "average_precision":
                float(ap),
        })

        for unidad_id, y, score in zip(
            validacion["unidad_id"],
            y_true,
            puntajes,
        ):

            oof.append({
                "unidad_id":
                    unidad_id,
                "fold":
                    int(fold),
                "etiqueta":
                    int(y),
                "modelo":
                    "Baseline prevalencia",
                "puntaje":
                    float(score),
            })

    return (
        resultados,
        oof,
        prevalencia,
    )


# ============================================================
# BASELINE 2
# RECENCIA
# ============================================================

def evaluar_baseline_recencia(
    df
):

    resultados = []

    oof = []

    for fold in sorted(
        df["fold"].unique()
    ):

        validacion = (
            df[
                df["fold"] == fold
            ]
            .copy()
        )

        y_true = (
            validacion[
                "etiqueta"
            ]
            .to_numpy()
        )

        # Mayor cantidad de días
        # desde el último viaje
        # = mayor riesgo esperado.
        puntajes = (
            validacion[
                "dias_desde_ultimo_viaje"
            ]
            .astype(float)
            .to_numpy()
        )

        ap = average_precision_score(
            y_true,
            puntajes,
        )

        resultados.append({
            "modelo":
                "Baseline recencia",
            "fold":
                int(fold),
            "average_precision":
                float(ap),
        })

        for unidad_id, y, score in zip(
            validacion["unidad_id"],
            y_true,
            puntajes,
        ):

            oof.append({
                "unidad_id":
                    unidad_id,
                "fold":
                    int(fold),
                "etiqueta":
                    int(y),
                "modelo":
                    "Baseline recencia",
                "puntaje":
                    float(score),
            })

    return (
        resultados,
        oof,
    )


# ============================================================
# RESUMIR RESULTADOS
# ============================================================

def resumir_resultados(
    resultados
):

    detalle = pd.DataFrame(
        resultados
    )

    resumen = (
        detalle
        .groupby(
            "modelo",
            as_index=False
        )
        .agg(
            ap_media=(
                "average_precision",
                "mean"
            ),
            ap_std=(
                "average_precision",
                "std"
            ),
        )
    )

    resumen[
        "ap_media"
    ] = (
        resumen[
            "ap_media"
        ]
        .round(6)
    )

    resumen[
        "ap_std"
    ] = (
        resumen[
            "ap_std"
        ]
        .round(6)
    )

    return detalle, resumen


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 1.4 - BLOQUE B")
    print("BASELINES")
    print("=" * 70)

    df = preparar_datos()

    print()
    print(
        f"Filas corte A : "
        f"{len(df):,}"
    )

    print(
        f"Positivos     : "
        f"{df['etiqueta'].sum():,}"
    )

    print(
        f"Folds         : "
        f"{df['fold'].nunique()}"
    )

    print(
        "Nulos recencia: "
        f"{df['dias_desde_ultimo_viaje'].isna().sum()}"
    )

    (
        resultados_constante,
        oof_constante,
        prevalencia,
    ) = evaluar_baseline_constante(
        df
    )

    (
        resultados_recencia,
        oof_recencia,
    ) = evaluar_baseline_recencia(
        df
    )

    resultados = (
        resultados_constante
        + resultados_recencia
    )

    oof = (
        oof_constante
        + oof_recencia
    )

    detalle, resumen = (
        resumir_resultados(
            resultados
        )
    )

    ruta_detalle = (
        OUTPUT_DIR
        / "fase1_4_baselines_por_fold.csv"
    )

    ruta_resumen = (
        OUTPUT_DIR
        / "fase1_4_baselines_resultados.csv"
    )

    ruta_oof = (
        OUTPUT_DIR
        / "fase1_4_baselines_oof.csv"
    )

    detalle.to_csv(
        ruta_detalle,
        index=False
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    pd.DataFrame(
        oof
    ).to_csv(
        ruta_oof,
        index=False
    )

    print()
    print("=" * 70)
    print("BASELINE 1 - PREVALENCIA")
    print("=" * 70)

    print(
        "Probabilidad asignada a todos: "
        f"{prevalencia:.6f}"
    )

    print(
        "Cuenta completa: "
        f"{POSITIVOS_ESPERADOS} "
        f"/ {FILAS_ESPERADAS} "
        f"= {prevalencia:.6f}"
    )

    print()
    print("=" * 70)
    print("RESULTADOS POR FOLD")
    print("=" * 70)

    print(
        detalle.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("RESUMEN DE BASELINES")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print(
        "[OK] Resultados guardados en:"
    )

    print(
        ruta_resumen
        .relative_to(
            PROJECT_ROOT
        )
    )

    print(
        ruta_detalle
        .relative_to(
            PROJECT_ROOT
        )
    )

    print(
        ruta_oof
        .relative_to(
            PROJECT_ROOT
        )
    )

    print()
    print("=" * 70)
    print("BLOQUE B COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()