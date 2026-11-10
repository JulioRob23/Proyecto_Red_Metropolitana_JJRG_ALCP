from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"

FASE1_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase1"
)

FASE2_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase2"
)

FOLDS_PATH = (
    FASE1_DIR
    / "fase1_4_folds.csv"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RANDOM_STATE = 42

N_REPEATS = 5

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310

HGB_CONFIG = {
    "learning_rate": 0.05,
    "max_iter": 150,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 30,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": RANDOM_STATE,
}


# ============================================================
# FEATURES
# ============================================================

FEATURES_NUMERICAS = [
    "viajes_7d",
    "viajes_14d",
    "viajes_28d",
    "dias_activos_28d",
    "dias_desde_ultimo_viaje",
    "cantidad_modos_28d",
    "proporcion_hora_pico",
    "proporcion_dia_habil",
    "gasto_total_28d",
    "gasto_promedio_28d",
    "proporcion_transmetro",
    "proporcion_transurbano",
    "proporcion_metroriel",
    "proporcion_aerometro",
    "es_multimodal",
]

FEATURES_CATEGORICAS = [
    "modo_mas_usado",
    "zona_mas_frecuente",
]

FEATURES = (
    FEATURES_NUMERICAS
    + FEATURES_CATEGORICAS
)


# ============================================================
# .ENV
# ============================================================

def cargar_env():

    valores = {}

    with open(
        ENV_PATH,
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
# POSTGRES
# ============================================================

def conectar_postgres():

    env = cargar_env()

    return psycopg2.connect(
        dbname=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        host=env["POSTGRES_HOST"],
        port=int(env["POSTGRES_PORT"]),
    )


# ============================================================
# CARGAR DATOS
# ============================================================

def cargar_datos():

    columnas = [
        "unidad_id",
        *FEATURES,
        "etiqueta",
    ]

    columnas_sql = ",\n            ".join(
        columnas
    )

    consulta = f"""
        SELECT
            {columnas_sql}
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

        nombres = [
            columna[0]
            for columna
            in cursor.description
        ]

        df = pd.DataFrame(
            filas,
            columns=nombres
        )

    finally:
        conexion.close()

    return df


# ============================================================
# PREPARACIÓN
# ============================================================

def preparar_datos():

    datos = cargar_datos()

    folds = pd.read_csv(
        FOLDS_PATH
    )

    df = datos.merge(
        folds[
            [
                "unidad_id",
                "fold",
                "etiqueta",
            ]
        ],
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
            "Cantidad incorrecta de filas."
        )

    if not (
        df["etiqueta_db"].astype(int)
        ==
        df["etiqueta_fold"].astype(int)
    ).all():

        raise RuntimeError(
            "Las etiquetas no coinciden."
        )

    df["etiqueta"] = (
        df["etiqueta_db"]
        .astype(int)
    )

    if int(
        df["etiqueta"].sum()
    ) != POSITIVOS_ESPERADOS:

        raise RuntimeError(
            "Cantidad incorrecta de positivos."
        )

    for columna in FEATURES_NUMERICAS:

        if columna == "es_multimodal":

            df[columna] = (
                df[columna]
                .astype(int)
                .astype(float)
            )

        else:

            df[columna] = (
                pd.to_numeric(
                    df[columna],
                    errors="coerce"
                )
                .astype(float)
            )

    for columna in FEATURES_CATEGORICAS:

        df[columna] = (
            df[columna]
            .astype("object")
        )

    if (
        df[FEATURES]
        .isna()
        .sum()
        .sum()
        != 0
    ):

        raise RuntimeError(
            "Se encontraron nulos."
        )

    return df


# ============================================================
# ONE HOT DENSO
# ============================================================

def crear_one_hot():

    try:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )

    except TypeError:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
        )


# ============================================================
# PIPELINE COMPLETO
# ============================================================

def crear_pipeline():

    numericas = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    categoricas = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                crear_one_hot(),
            ),
        ]
    )

    preprocesador = ColumnTransformer(
        transformers=[
            (
                "num",
                numericas,
                FEATURES_NUMERICAS,
            ),
            (
                "cat",
                categoricas,
                FEATURES_CATEGORICAS,
            ),
        ],
        remainder="drop",
    )

    modelo = HistGradientBoostingClassifier(
        **HGB_CONFIG
    )

    return Pipeline(
        steps=[
            (
                "preprocesamiento",
                preprocesador,
            ),
            (
                "modelo",
                modelo,
            ),
        ]
    )


# ============================================================
# PERMUTATION IMPORTANCE
# ============================================================

def calcular_importancias(df):

    resultados = []

    for fold in sorted(
        df["fold"].unique()
    ):

        print()
        print("=" * 70)
        print(
            f"FOLD {fold} / 5"
        )
        print("=" * 70)

        train = (
            df[
                df["fold"] != fold
            ]
            .copy()
        )

        validacion = (
            df[
                df["fold"] == fold
            ]
            .copy()
        )

        X_train = (
            train[FEATURES]
        )

        y_train = (
            train[
                "etiqueta"
            ]
            .to_numpy()
        )

        X_val = (
            validacion[FEATURES]
        )

        y_val = (
            validacion[
                "etiqueta"
            ]
            .to_numpy()
        )

        pipeline = crear_pipeline()

        print(
            "[1/2] Entrenando ensemble..."
        )

        pipeline.fit(
            X_train,
            y_train
        )

        print(
            "[2/2] Calculando permutation "
            f"importance ({N_REPEATS} repeticiones)..."
        )

        inicio = perf_counter()

        importancia = permutation_importance(
            pipeline,
            X_val,
            y_val,
            scoring="average_precision",
            n_repeats=N_REPEATS,
            random_state=(
                RANDOM_STATE
                + int(fold)
            ),
            n_jobs=-1,
        )

        duracion = (
            perf_counter()
            - inicio
        )

        for indice, feature in enumerate(
            FEATURES
        ):

            resultados.append({
                "fold":
                    int(fold),

                "feature":
                    feature,

                "importancia_media_fold":
                    float(
                        importancia[
                            "importances_mean"
                        ][indice]
                    ),

                "importancia_std_fold":
                    float(
                        importancia[
                            "importances_std"
                        ][indice]
                    ),
            })

        ranking_fold = pd.DataFrame(
            resultados
        )

        ranking_fold = (
            ranking_fold[
                ranking_fold[
                    "fold"
                ] == fold
            ]
            .sort_values(
                "importancia_media_fold",
                ascending=False
            )
            .head(5)
        )

        print()
        print(
            ranking_fold[
                [
                    "feature",
                    "importancia_media_fold",
                ]
            ]
            .to_string(
                index=False
            )
        )

        print(
            f"\n[OK] Fold {fold}: "
            f"{duracion:.2f} s"
        )

    return pd.DataFrame(
        resultados
    )


# ============================================================
# CONSOLIDAR FOLDS
# ============================================================

def consolidar_importancias(
    detalle
):

    resumen = (
        detalle
        .groupby(
            "feature",
            as_index=False
        )
        .agg(
            importancia_media=(
                "importancia_media_fold",
                "mean"
            ),

            importancia_std_entre_folds=(
                "importancia_media_fold",
                "std"
            ),
        )
    )

    resumen = (
        resumen
        .sort_values(
            "importancia_media",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    resumen[
        "ranking"
    ] = (
        np.arange(
            1,
            len(resumen) + 1
        )
    )

    return resumen[
        [
            "ranking",
            "feature",
            "importancia_media",
            "importancia_std_entre_folds",
        ]
    ]


# ============================================================
# GRÁFICA TOP 10
# ============================================================

def crear_grafica(
    resumen
):

    top10 = (
        resumen
        .head(10)
        .sort_values(
            "importancia_media",
            ascending=True
        )
    )

    figura = plt.figure(
        figsize=(10, 6)
    )

    plt.barh(
        top10["feature"],
        top10["importancia_media"],
        xerr=top10[
            "importancia_std_entre_folds"
        ],
        capsize=3,
    )

    plt.xlabel(
        "Disminución de Average Precision"
    )

    plt.ylabel(
        "Feature"
    )

    plt.title(
        "Top 10 permutation importances "
        "en validación"
    )

    plt.tight_layout()

    ruta = (
        FASE2_DIR
        / "fase2_1_top10_permutation_importance.png"
    )

    figura.savefig(
        ruta,
        dpi=160,
        bbox_inches="tight"
    )

    plt.close(
        figura
    )

    return ruta


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 2.1 - BLOQUE D")
    print("PERMUTATION IMPORTANCE")
    print("=" * 70)

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "- La importancia se calculará "
        "exclusivamente en validación."
    )

    print(
        "- Se reutilizan exactamente "
        "los 5 folds oficiales."
    )

    print(
        "- El corte B no se consulta."
    )

    df = preparar_datos()

    detalle = calcular_importancias(
        df
    )

    resumen = consolidar_importancias(
        detalle
    )

    ruta_detalle = (
        FASE2_DIR
        / "fase2_1_permutation_por_fold.csv"
    )

    ruta_resumen = (
        FASE2_DIR
        / "fase2_1_permutation_importance.csv"
    )

    detalle.to_csv(
        ruta_detalle,
        index=False
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    ruta_grafica = crear_grafica(
        resumen
    )

    print()
    print("=" * 70)
    print("TOP 10 FEATURES")
    print("=" * 70)

    print(
        resumen
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)

    for ruta in [
        ruta_detalle,
        ruta_resumen,
        ruta_grafica,
    ]:

        print(
            "[OK] "
            + str(
                ruta.relative_to(
                    PROJECT_ROOT
                )
            )
        )

    print()
    print("=" * 70)
    print("BLOQUE D COMPLETADO")
    print("=" * 70)

    print(
        "[OK] Importancias calculadas "
        "sobre validación."
    )

    print(
        "[OK] Corte B sigue intacto."
    )


if __name__ == "__main__":
    main()