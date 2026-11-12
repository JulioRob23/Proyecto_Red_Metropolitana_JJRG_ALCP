from pathlib import Path
from datetime import datetime
import hashlib
import json
from time import perf_counter

import joblib
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

CONFIG_PATH = (
    PROJECT_ROOT
    / "modeling"
    / "fase2_2_config_modelo_congelado.json"
)

MODELS_DIR = (
    PROJECT_ROOT
    / "models"
)

MODELS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MODEL_PATH = (
    MODELS_DIR
    / "modelo_churn_p2_hgb_v1.joblib"
)

METADATA_PATH = (
    MODELS_DIR
    / "modelo_churn_p2_hgb_v1.metadata.json"
)

FASE2_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase2"
)

RESUMEN_PATH = (
    FASE2_DIR
    / "fase2_4_modelo_guardado.csv"
)


# ============================================================
# CONTROLES
# ============================================================

FILAS_A_ESPERADAS = 59999
POSITIVOS_A_ESPERADOS = 8310


# ============================================================
# CONFIGURACIÓN CONGELADA
# ============================================================

def cargar_config():

    if not CONFIG_PATH.exists():

        raise FileNotFoundError(
            "No se encontró la configuración "
            "congelada de Fase 2.2."
        )

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        config = json.load(
            archivo
        )

    if (
        config["estado"]
        != "CONGELADO_ANTES_TEST_B"
    ):

        raise RuntimeError(
            "La configuración no corresponde "
            "al modelo congelado."
        )

    if (
        config["modelo"]["clase"]
        != "HistGradientBoostingClassifier"
    ):

        raise RuntimeError(
            "El modelo congelado no coincide."
        )

    return config


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


def conectar_postgres():

    env = cargar_env()

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
# CARGAR A
# ============================================================

def cargar_corte_a(
    features
):

    columnas = [
        "unidad_id",
        *features,
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
# TIPOS
# ============================================================

def preparar_datos(
    df,
    features
):

    df = df.copy()

    categoricas = [
        "modo_mas_usado",
        "zona_mas_frecuente",
    ]

    numericas = [
        feature
        for feature in features
        if feature not in categoricas
    ]

    for columna in numericas:

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

    for columna in categoricas:

        df[columna] = (
            df[columna]
            .astype("object")
        )

    df["etiqueta"] = (
        df["etiqueta"]
        .astype(int)
    )

    if (
        df[features]
        .isna()
        .sum()
        .sum()
        != 0
    ):

        raise RuntimeError(
            "Se encontraron valores nulos."
        )

    return df


# ============================================================
# ONE HOT
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
# PIPELINE
# ============================================================

def crear_pipeline(
    config
):

    features = config[
        "features"
    ]

    categoricas = [
        "modo_mas_usado",
        "zona_mas_frecuente",
    ]

    numericas = [
        feature
        for feature in features
        if feature not in categoricas
    ]

    preprocesamiento = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="median"
                            ),
                        ),
                    ]
                ),
                numericas,
            ),
            (
                "cat",
                Pipeline(
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
                ),
                categoricas,
            ),
        ],
        remainder="drop",
    )

    parametros = config[
        "modelo"
    ][
        "parametros"
    ]

    modelo = (
        HistGradientBoostingClassifier(
            **parametros
        )
    )

    return Pipeline(
        steps=[
            (
                "preprocesamiento",
                preprocesamiento,
            ),
            (
                "modelo",
                modelo,
            ),
        ]
    )


# ============================================================
# SHA256
# ============================================================

def calcular_sha256(
    ruta
):

    hash_obj = hashlib.sha256()

    with open(
        ruta,
        "rb"
    ) as archivo:

        while True:

            bloque = archivo.read(
                1024 * 1024
            )

            if not bloque:
                break

            hash_obj.update(
                bloque
            )

    return hash_obj.hexdigest()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 74)
    print("FASE 2.4 - BLOQUE A")
    print("ENTRENAR Y GUARDAR MODELO FINAL")
    print("=" * 74)

    config = cargar_config()

    features = config[
        "features"
    ]

    umbral = float(
        config[
            "umbral"
        ][
            "valor"
        ]
    )

    print()
    print("CONFIGURACIÓN FINAL")
    print("-" * 74)

    print(
        f"Versión : "
        f"{config['version']}"
    )

    print(
        f"Modelo  : "
        f"{config['modelo']['clase']}"
    )

    print(
        f"Umbral  : "
        f"{umbral:.12f}"
    )

    print(
        f"Features: "
        f"{len(features)}"
    )

    # ----------------------------------------
    # A
    # ----------------------------------------

    print()
    print(
        "[1/5] Cargando corte A..."
    )

    df = cargar_corte_a(
        features
    )

    df = preparar_datos(
        df,
        features
    )

    if len(df) != FILAS_A_ESPERADAS:

        raise RuntimeError(
            "Cantidad inesperada de filas A."
        )

    if (
        int(df["etiqueta"].sum())
        != POSITIVOS_A_ESPERADOS
    ):

        raise RuntimeError(
            "Cantidad inesperada de positivos A."
        )

    print(
        f"[OK] Filas     : "
        f"{len(df):,}"
    )

    print(
        f"[OK] Positivos : "
        f"{df['etiqueta'].sum():,}"
    )

    # ----------------------------------------
    # Entrenar
    # ----------------------------------------

    print()
    print(
        "[2/5] Entrenando pipeline final "
        "únicamente con A..."
    )

    pipeline = crear_pipeline(
        config
    )

    inicio = perf_counter()

    pipeline.fit(
        df[features],
        df["etiqueta"]
    )

    tiempo_entrenamiento = (
        perf_counter()
        - inicio
    )

    print(
        f"[OK] Entrenamiento: "
        f"{tiempo_entrenamiento:.2f} s"
    )

    # ----------------------------------------
    # Sanity check A
    # NO es nueva validación.
    # ----------------------------------------

    print()
    print(
        "[3/5] Verificando pipeline..."
    )

    probabilidades_a = (
        pipeline
        .predict_proba(
            df[features]
        )[:, 1]
    )

    ap_train_a = (
        average_precision_score(
            df["etiqueta"],
            probabilidades_a
        )
    )

    print(
        f"[OK] AP entrenamiento A: "
        f"{ap_train_a:.6f}"
    )

    # ----------------------------------------
    # Guardar
    # ----------------------------------------

    print()
    print(
        "[4/5] Guardando modelo..."
    )

    joblib.dump(
        pipeline,
        MODEL_PATH,
        compress=3,
    )

    if not MODEL_PATH.exists():

        raise RuntimeError(
            "El modelo no fue guardado."
        )

    tamanio_bytes = (
        MODEL_PATH.stat().st_size
    )

    sha256 = calcular_sha256(
        MODEL_PATH
    )

    print(
        f"[OK] Modelo: "
        f"{MODEL_PATH.name}"
    )

    print(
        f"[OK] Tamaño: "
        f"{tamanio_bytes / 1024 / 1024:.2f} MB"
    )

    print(
        f"[OK] SHA256: "
        f"{sha256}"
    )

    # ----------------------------------------
    # Verificar que carga sin entrenar
    # ----------------------------------------

    print()
    print(
        "[5/5] Recargando modelo "
        "desde disco..."
    )

    modelo_cargado = (
        joblib.load(
            MODEL_PATH
        )
    )

    prueba = (
        df[features]
        .head(100)
    )

    pred_original = (
        pipeline
        .predict_proba(
            prueba
        )[:, 1]
    )

    pred_cargado = (
        modelo_cargado
        .predict_proba(
            prueba
        )[:, 1]
    )

    diferencia_maxima = float(
        abs(
            pred_original
            - pred_cargado
        ).max()
    )

    if diferencia_maxima != 0:

        raise RuntimeError(
            "Las predicciones del modelo "
            "recargado no son idénticas."
        )

    print(
        "[OK] Modelo recargado "
        "correctamente."
    )

    print(
        "[OK] Predicciones idénticas "
        "después de cargar."
    )

    # ----------------------------------------
    # Metadata
    # ----------------------------------------

    metadata = {
        "version":
            config["version"],

        "archivo_modelo":
            MODEL_PATH.name,

        "sha256":
            sha256,

        "fecha_creacion":
            datetime.now()
            .astimezone()
            .isoformat(),

        "modelo":
            config[
                "modelo"
            ],

        "entrenamiento": {
            "corte":
                "A",

            "fecha_corte":
                "2026-07-01",

            "filas":
                len(df),

            "positivos":
                int(
                    df[
                        "etiqueta"
                    ].sum()
                ),

            "segundos":
                tiempo_entrenamiento,
        },

        "features":
            features,

        "umbral":
            umbral,

        "metrica_cv_a":
            config[
                "metrica_seleccion"
            ],

        "test_b": {
            "ya_evaluado":
                True,

            "nota":
                (
                    "El resultado B fue registrado "
                    "en Fase 2.2 y no se utilizó "
                    "para reajustar el modelo."
                ),
        },

        "regla_produccion":
            (
                "El modelo se carga desde disco "
                "y no debe reentrenarse dentro "
                "de predecir.py."
            ),
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            metadata,
            archivo,
            indent=2,
            ensure_ascii=False,
        )

    # ----------------------------------------
    # Resumen CSV
    # ----------------------------------------

    resumen = pd.DataFrame([
        {
            "version":
                config["version"],

            "modelo":
                config[
                    "modelo"
                ][
                    "clase"
                ],

            "archivo":
                MODEL_PATH.name,

            "filas_entrenamiento":
                len(df),

            "positivos_entrenamiento":
                int(
                    df[
                        "etiqueta"
                    ].sum()
                ),

            "umbral":
                umbral,

            "ap_cv_a":
                config[
                    "metrica_seleccion"
                ][
                    "ap_validacion_media"
                ],

            "ap_train_a_sanity":
                ap_train_a,

            "segundos_entrenamiento":
                tiempo_entrenamiento,

            "tamanio_bytes":
                tamanio_bytes,

            "sha256":
                sha256,

            "diferencia_pred_recarga":
                diferencia_maxima,
        }
    ])

    resumen.to_csv(
        RESUMEN_PATH,
        index=False
    )

    print()
    print("=" * 74)
    print("MODELO FINAL GUARDADO")
    print("=" * 74)

    print(
        f"Archivo       : "
        f"models/{MODEL_PATH.name}"
    )

    print(
        f"Versión       : "
        f"{config['version']}"
    )

    print(
        f"Entrenado con : "
        f"corte A ({len(df):,} filas)"
    )

    print(
        f"Umbral        : "
        f"{umbral:.6f}"
    )

    print(
        f"AP CV A       : "
        f"{config['metrica_seleccion']['ap_validacion_media']:.6f}"
    )

    print(
        f"SHA256        : "
        f"{sha256}"
    )

    print()
    print(
        "[OK] Pipeline completo guardado."
    )

    print(
        "[OK] Incluye preprocesamiento "
        "+ HistGradientBoosting."
    )

    print(
        "[OK] El archivo puede cargarse "
        "sin reentrenar."
    )

    print(
        "[OK] Corte B no fue consultado."
    )

    print()
    print("=" * 74)
    print("BLOQUE 2.4-A COMPLETADO")
    print("=" * 74)


if __name__ == "__main__":
    main()