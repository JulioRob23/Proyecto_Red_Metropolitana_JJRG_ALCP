from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import psycopg2

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
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

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310

# Ensemble único y reproducible.
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
# DATOS
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
            for columna in cursor.description
        ]

        df = pd.DataFrame(
            filas,
            columns=nombres
        )

    finally:
        conexion.close()

    return df


# ============================================================
# PREPARAR DATOS
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
            "El corte A no contiene "
            "59,999 filas."
        )

    if not (
        df["etiqueta_db"].astype(int)
        ==
        df["etiqueta_fold"].astype(int)
    ).all():

        raise RuntimeError(
            "Las etiquetas no coinciden "
            "con los folds oficiales."
        )

    df["etiqueta"] = (
        df["etiqueta_db"]
        .astype(int)
    )

    if (
        int(df["etiqueta"].sum())
        != POSITIVOS_ESPERADOS
    ):

        raise RuntimeError(
            "Los positivos no coinciden."
        )

    # ----------------------------------------
    # Conversión explícita de numéricas
    # ----------------------------------------

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

    # ----------------------------------------
    # Categóricas
    # ----------------------------------------

    for columna in FEATURES_CATEGORICAS:

        df[columna] = (
            df[columna]
            .astype("object")
        )

    # Ya comprobamos 0 nulos en A.
    # Si la conversión creó alguno, detenemos.
    nulos = int(
        df[FEATURES]
        .isna()
        .sum()
        .sum()
    )

    if nulos != 0:

        raise RuntimeError(
            "La conversión de features "
            f"produjo {nulos} valores nulos."
        )

    return df


# ============================================================
# ONE-HOT DENSO
# HistGradientBoosting requiere matriz densa
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
# PREPROCESAMIENTO
# ============================================================

def crear_preprocesador():

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

    return ColumnTransformer(
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


# ============================================================
# ENTRENAMIENTO CV
# ============================================================

def ejecutar_cv(df):

    resultados = []
    oof = []

    folds = sorted(
        df["fold"].unique()
    )

    inicio_total = perf_counter()

    for fold in folds:

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

        X_train = train[
            FEATURES
        ]

        y_train = (
            train["etiqueta"]
            .to_numpy()
        )

        X_val = validacion[
            FEATURES
        ]

        y_val = (
            validacion["etiqueta"]
            .to_numpy()
        )

        # ------------------------------------
        # Preprocesamiento aprendido
        # únicamente con training
        # ------------------------------------

        preprocesador = (
            crear_preprocesador()
        )

        inicio_pre = perf_counter()

        X_train_proc = (
            preprocesador
            .fit_transform(
                X_train
            )
        )

        X_val_proc = (
            preprocesador
            .transform(
                X_val
            )
        )

        tiempo_pre = (
            perf_counter()
            - inicio_pre
        )

        print(
            "[OK] Preprocesamiento: "
            f"{tiempo_pre:.2f} s"
        )

        print(
            "Dimensiones procesadas:"
        )

        print(
            f"  train      : "
            f"{X_train_proc.shape}"
        )

        print(
            f"  validación : "
            f"{X_val_proc.shape}"
        )

        # ------------------------------------
        # Modelo
        # ------------------------------------

        modelo = (
            HistGradientBoostingClassifier(
                **HGB_CONFIG
            )
        )

        inicio_modelo = perf_counter()

        modelo.fit(
            X_train_proc,
            y_train
        )

        tiempo_modelo = (
            perf_counter()
            - inicio_modelo
        )

        # ------------------------------------
        # Probabilidades TRAIN
        # ------------------------------------

        prob_train = (
            modelo
            .predict_proba(
                X_train_proc
            )[:, 1]
        )

        ap_train = (
            average_precision_score(
                y_train,
                prob_train
            )
        )

        # ------------------------------------
        # Probabilidades VALIDACIÓN
        # ------------------------------------

        prob_val = (
            modelo
            .predict_proba(
                X_val_proc
            )[:, 1]
        )

        ap_val = (
            average_precision_score(
                y_val,
                prob_val
            )
        )

        brecha = (
            ap_train
            - ap_val
        )

        resultados.append({
            "modelo":
                "HistGradientBoosting",
            "fold":
                int(fold),
            "ap_train":
                float(ap_train),
            "ap_validacion":
                float(ap_val),
            "brecha_train_validacion":
                float(brecha),
            "segundos_preprocesamiento":
                round(
                    tiempo_pre,
                    4
                ),
            "segundos_entrenamiento":
                round(
                    tiempo_modelo,
                    4
                ),
        })

        # ------------------------------------
        # OOF
        # ------------------------------------

        for (
            unidad_id,
            etiqueta,
            probabilidad,
        ) in zip(
            validacion[
                "unidad_id"
            ],
            y_val,
            prob_val,
        ):

            oof.append({
                "unidad_id":
                    unidad_id,
                "fold":
                    int(fold),
                "etiqueta":
                    int(etiqueta),
                "modelo":
                    "HistGradientBoosting",
                "probabilidad":
                    float(probabilidad),
            })

        print()
        print(
            f"AP train      : "
            f"{ap_train:.6f}"
        )

        print(
            f"AP validación : "
            f"{ap_val:.6f}"
        )

        print(
            f"Brecha        : "
            f"{brecha:.6f}"
        )

        print(
            f"Entrenamiento : "
            f"{tiempo_modelo:.2f} s"
        )

    duracion_total = (
        perf_counter()
        - inicio_total
    )

    return (
        pd.DataFrame(
            resultados
        ),
        pd.DataFrame(
            oof
        ),
        duracion_total,
    )


# ============================================================
# RESUMEN
# ============================================================

def resumir_resultados(
    detalle
):

    resumen = pd.DataFrame([
        {
            "modelo":
                "HistGradientBoosting",

            "ap_train_media":
                detalle[
                    "ap_train"
                ].mean(),

            "ap_train_std":
                detalle[
                    "ap_train"
                ].std(),

            "ap_validacion_media":
                detalle[
                    "ap_validacion"
                ].mean(),

            "ap_validacion_std":
                detalle[
                    "ap_validacion"
                ].std(),

            "brecha_media":
                detalle[
                    "brecha_train_validacion"
                ].mean(),

            "tiempo_entrenamiento_medio_s":
                detalle[
                    "segundos_entrenamiento"
                ].mean(),
        }
    ])

    columnas_numericas = [
        "ap_train_media",
        "ap_train_std",
        "ap_validacion_media",
        "ap_validacion_std",
        "brecha_media",
        "tiempo_entrenamiento_medio_s",
    ]

    for columna in columnas_numericas:

        resumen[columna] = (
            resumen[columna]
            .round(6)
        )

    return resumen


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 2.1 - BLOQUE B")
    print("HISTGRADIENTBOOSTING")
    print("=" * 70)

    print()
    print(
        "Configuración:"
    )

    for clave, valor in (
        HGB_CONFIG.items()
    ):

        print(
            f"  {clave}: {valor}"
        )

    df = preparar_datos()

    print()
    print(
        f"Filas A    : {len(df):,}"
    )

    print(
        f"Positivos  : "
        f"{df['etiqueta'].sum():,}"
    )

    print(
        f"Folds      : "
        f"{df['fold'].nunique()}"
    )

    detalle, oof, duracion = (
        ejecutar_cv(
            df
        )
    )

    resumen = resumir_resultados(
        detalle
    )

    # ----------------------------------------
    # Guardar
    # ----------------------------------------

    ruta_detalle = (
        FASE2_DIR
        / "fase2_1_ensemble_por_fold.csv"
    )

    ruta_resumen = (
        FASE2_DIR
        / "fase2_1_ensemble_resumen.csv"
    )

    ruta_oof = (
        FASE2_DIR
        / "fase2_1_ensemble_oof.csv"
    )

    detalle.to_csv(
        ruta_detalle,
        index=False
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    oof.to_csv(
        ruta_oof,
        index=False
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
    print("RESUMEN ENSEMBLE")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print(
        f"Tiempo total CV: "
        f"{duracion:.2f} s"
    )

    print()
    print("=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)

    for ruta in [
        ruta_detalle,
        ruta_resumen,
        ruta_oof,
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
    print("BLOQUE B COMPLETADO")
    print("=" * 70)

    print(
        "[OK] Ensemble evaluado "
        "solo con corte A."
    )

    print(
        "[OK] Se usaron los mismos "
        "5 folds de Fase 1."
    )

    print(
        "[OK] Corte B sigue sin "
        "ser utilizado."
    )


if __name__ == "__main__":
    main()