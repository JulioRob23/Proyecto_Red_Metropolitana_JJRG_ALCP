from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import psycopg2

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


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

ENSEMBLE_FOLDS_PATH = (
    FASE2_DIR
    / "fase2_1_ensemble_por_fold.csv"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RANDOM_STATE = 42
MAX_ITER = 3000

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310

# Mejores configuraciones de Fase 1.4
LOGISTICAS = {
    "Logística L1": {
        "tipo": "l1",
        "lambda": 10.0,
        "C": 0.1,
    },
    "Logística L2": {
        "tipo": "l2",
        "lambda": 100.0,
        "C": 0.01,
    },
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
# CARGAR CORTE A
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
            "Cantidad de filas incorrecta."
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
            "Cantidad de positivos incorrecta."
        )

    # Numéricas
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

    # Categóricas
    for columna in FEATURES_CATEGORICAS:

        df[columna] = (
            df[columna]
            .astype("object")
        )

    if df[FEATURES].isna().sum().sum() != 0:

        raise RuntimeError(
            "Se encontraron nulos "
            "después de la conversión."
        )

    return df


# ============================================================
# ONE HOT
# ============================================================

def crear_one_hot():

    try:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )

    except TypeError:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=True,
        )


# ============================================================
# PREPROCESADOR LOGÍSTICA
# Igual al de Fase 1.4
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
            (
                "scaler",
                StandardScaler(),
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
# CREAR LOGÍSTICA
# Compatible con sklearn actual
# ============================================================

def crear_logistica(
    tipo,
    C,
):

    if tipo == "l1":
        l1_ratio = 1.0

    elif tipo == "l2":
        l1_ratio = 0.0

    else:
        raise ValueError(
            "Tipo de regularización inválido."
        )

    return LogisticRegression(
        C=C,
        l1_ratio=l1_ratio,
        solver="liblinear",
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
    )


# ============================================================
# EVALUAR BASELINES
# ============================================================

def evaluar_baselines(
    df
):

    resultados = []

    prevalencia_global = (
        df["etiqueta"].mean()
    )

    for fold in sorted(
        df["fold"].unique()
    ):

        train = (
            df[
                df["fold"] != fold
            ]
        )

        validacion = (
            df[
                df["fold"] == fold
            ]
        )

        y_train = (
            train[
                "etiqueta"
            ]
            .to_numpy()
        )

        y_val = (
            validacion[
                "etiqueta"
            ]
            .to_numpy()
        )

        # ------------------------------------
        # Baseline prevalencia
        # ------------------------------------

        score_train = np.full(
            len(train),
            prevalencia_global,
        )

        score_val = np.full(
            len(validacion),
            prevalencia_global,
        )

        resultados.append({
            "modelo":
                "Baseline prevalencia",
            "fold":
                int(fold),
            "ap_train":
                average_precision_score(
                    y_train,
                    score_train
                ),
            "ap_validacion":
                average_precision_score(
                    y_val,
                    score_val
                ),
        })

        # ------------------------------------
        # Baseline recencia
        # ------------------------------------

        score_train = (
            train[
                "dias_desde_ultimo_viaje"
            ]
            .to_numpy()
        )

        score_val = (
            validacion[
                "dias_desde_ultimo_viaje"
            ]
            .to_numpy()
        )

        resultados.append({
            "modelo":
                "Baseline recencia",
            "fold":
                int(fold),
            "ap_train":
                average_precision_score(
                    y_train,
                    score_train
                ),
            "ap_validacion":
                average_precision_score(
                    y_val,
                    score_val
                ),
        })

    return resultados


# ============================================================
# EVALUAR LOGÍSTICAS
# ============================================================

def evaluar_logisticas(
    df
):

    resultados = []

    for nombre_modelo, config in (
        LOGISTICAS.items()
    ):

        print()
        print("=" * 70)
        print(nombre_modelo.upper())
        print("=" * 70)

        for fold in sorted(
            df["fold"].unique()
        ):

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

            preprocesador = (
                crear_preprocesador()
            )

            X_train = (
                preprocesador
                .fit_transform(
                    train[FEATURES]
                )
            )

            X_val = (
                preprocesador
                .transform(
                    validacion[
                        FEATURES
                    ]
                )
            )

            y_train = (
                train[
                    "etiqueta"
                ]
                .to_numpy()
            )

            y_val = (
                validacion[
                    "etiqueta"
                ]
                .to_numpy()
            )

            modelo = crear_logistica(
                tipo=config["tipo"],
                C=config["C"],
            )

            inicio = perf_counter()

            modelo.fit(
                X_train,
                y_train
            )

            tiempo = (
                perf_counter()
                - inicio
            )

            prob_train = (
                modelo
                .predict_proba(
                    X_train
                )[:, 1]
            )

            prob_val = (
                modelo
                .predict_proba(
                    X_val
                )[:, 1]
            )

            ap_train = (
                average_precision_score(
                    y_train,
                    prob_train
                )
            )

            ap_val = (
                average_precision_score(
                    y_val,
                    prob_val
                )
            )

            resultados.append({
                "modelo":
                    nombre_modelo,
                "fold":
                    int(fold),
                "ap_train":
                    float(ap_train),
                "ap_validacion":
                    float(ap_val),
            })

            print(
                f"Fold {fold}: "
                f"train={ap_train:.6f} | "
                f"val={ap_val:.6f} | "
                f"{tiempo:.2f}s"
            )

    return resultados


# ============================================================
# CARGAR ENSEMBLE YA CALCULADO
# ============================================================

def cargar_ensemble():

    if not ENSEMBLE_FOLDS_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_1_ensemble_por_fold.csv"
        )

    ensemble = pd.read_csv(
        ENSEMBLE_FOLDS_PATH
    )

    resultados = []

    for _, fila in (
        ensemble.iterrows()
    ):

        resultados.append({
            "modelo":
                "HistGradientBoosting",
            "fold":
                int(
                    fila["fold"]
                ),
            "ap_train":
                float(
                    fila["ap_train"]
                ),
            "ap_validacion":
                float(
                    fila["ap_validacion"]
                ),
        })

    return resultados


# ============================================================
# RESUMEN FINAL
# ============================================================

def crear_resumen(
    detalle
):

    resumen = (
        detalle
        .groupby(
            "modelo",
            as_index=False
        )
        .agg(
            ap_train_media=(
                "ap_train",
                "mean"
            ),
            ap_train_std=(
                "ap_train",
                "std"
            ),
            ap_validacion_media=(
                "ap_validacion",
                "mean"
            ),
            ap_validacion_std=(
                "ap_validacion",
                "std"
            ),
        )
    )

    resumen[
        "brecha_media"
    ] = (
        resumen[
            "ap_train_media"
        ]
        -
        resumen[
            "ap_validacion_media"
        ]
    )

    columnas = [
        "ap_train_media",
        "ap_train_std",
        "ap_validacion_media",
        "ap_validacion_std",
        "brecha_media",
    ]

    for columna in columnas:

        resumen[columna] = (
            resumen[columna]
            .round(6)
        )

    return (
        resumen
        .sort_values(
            "ap_validacion_media",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 2.1 - BLOQUE C")
    print("COMPARACIÓN Y SESGO-VARIANZA")
    print("=" * 70)

    df = preparar_datos()

    resultados = []

    print()
    print(
        "[1/3] Evaluando baselines..."
    )

    resultados.extend(
        evaluar_baselines(
            df
        )
    )

    print(
        "[OK] Baselines terminados."
    )

    print()
    print(
        "[2/3] Evaluando logísticas..."
    )

    resultados.extend(
        evaluar_logisticas(
            df
        )
    )

    print()
    print(
        "[3/3] Cargando ensemble..."
    )

    resultados.extend(
        cargar_ensemble()
    )

    detalle = pd.DataFrame(
        resultados
    )

    detalle[
        "brecha_train_validacion"
    ] = (
        detalle[
            "ap_train"
        ]
        -
        detalle[
            "ap_validacion"
        ]
    )

    resumen = crear_resumen(
        detalle
    )

    ruta_detalle = (
        FASE2_DIR
        / "fase2_1_comparacion_por_fold.csv"
    )

    ruta_resumen = (
        FASE2_DIR
        / "fase2_1_comparacion_modelos.csv"
    )

    detalle.to_csv(
        ruta_detalle,
        index=False
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    print()
    print("=" * 70)
    print("COMPARACIÓN FINAL")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("REFERENCIA PRINCIPAL")
    print("=" * 70)

    logistica = (
        resumen[
            resumen["modelo"]
            == "Logística L2"
        ]
        .iloc[0]
    )

    ensemble = (
        resumen[
            resumen["modelo"]
            == "HistGradientBoosting"
        ]
        .iloc[0]
    )

    mejora = (
        ensemble[
            "ap_validacion_media"
        ]
        -
        logistica[
            "ap_validacion_media"
        ]
    )

    print(
        "Logística L2 AP val : "
        f"{logistica['ap_validacion_media']:.6f}"
    )

    print(
        "Ensemble AP val      : "
        f"{ensemble['ap_validacion_media']:.6f}"
    )

    print(
        "Mejora absoluta      : "
        f"{mejora:.6f}"
    )

    print(
        "Brecha Logística L2  : "
        f"{logistica['brecha_media']:.6f}"
    )

    print(
        "Brecha Ensemble      : "
        f"{ensemble['brecha_media']:.6f}"
    )

    print()
    print("=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)

    print(
        "[OK] "
        + str(
            ruta_detalle.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "[OK] "
        + str(
            ruta_resumen.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print("=" * 70)
    print("BLOQUE C COMPLETADO")
    print("=" * 70)

    print(
        "[OK] Comparación realizada "
        "solo con corte A."
    )

    print(
        "[OK] Corte B sigue intacto."
    )


if __name__ == "__main__":
    main()