from pathlib import Path
from datetime import datetime
import argparse
import json
import subprocess
from time import perf_counter

import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"

FASE2_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase2"
)

CONFIG_PATH = (
    PROJECT_ROOT
    / "modeling"
    / "fase2_2_config_modelo_congelado.json"
)

LOCK_PATH = (
    FASE2_DIR
    / "fase2_2_TEST_B_EJECUTADO.json"
)

RESULTADO_PATH = (
    FASE2_DIR
    / "fase2_2_test_b_resultado.csv"
)

MATRIZ_PATH = (
    FASE2_DIR
    / "fase2_2_matriz_confusion_b.csv"
)

MATRIZ_PNG_PATH = (
    FASE2_DIR
    / "fase2_2_matriz_confusion_b.png"
)

BITACORA_PATH = (
    FASE2_DIR
    / "fase2_2_test_b_bitacora.md"
)


# ============================================================
# COMMIT EN EL QUE SE CONGELÓ EL MODELO
# ============================================================

PRETEST_COMMIT = (
    "e8ae9366345c61fccb82e65519533bf00fe450c8"
)


# ============================================================
# CONTROLES ESPERADOS
# ============================================================

FILAS_A_ESPERADAS = 59999
POSITIVOS_A_ESPERADOS = 8310

FILAS_B_ESPERADAS = 54279


# ============================================================
# GIT
# ============================================================

def ejecutar_git(*args):

    resultado = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    return resultado.stdout.strip()


def obtener_commit_actual():

    return ejecutar_git(
        "rev-parse",
        "HEAD"
    )


def verificar_repo_limpio():

    estado = ejecutar_git(
        "status",
        "--porcelain"
    )

    if estado:

        raise RuntimeError(
            "El repositorio tiene cambios "
            "sin commit.\n\n"
            + estado
        )


# ============================================================
# CONFIGURACIÓN CONGELADA
# ============================================================

def cargar_config():

    if not CONFIG_PATH.exists():

        raise FileNotFoundError(
            "No existe la configuración "
            "congelada."
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
        config.get("estado")
        != "CONGELADO_ANTES_TEST_B"
    ):

        raise RuntimeError(
            "La configuración no está "
            "marcada como congelada."
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
# PIPELINE EXACTO DEL ENSEMBLE
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

    pipe_num = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    pipe_cat = Pipeline(
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

    preprocesamiento = ColumnTransformer(
        transformers=[
            (
                "num",
                pipe_num,
                numericas,
            ),
            (
                "cat",
                pipe_cat,
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
# CARGAR UN CORTE
# ============================================================

def cargar_corte(
    corte,
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
        WHERE corte = %s
        ORDER BY unidad_id;
    """

    conexion = conectar_postgres()

    try:

        cursor = conexion.cursor()

        cursor.execute(
            consulta,
            (corte,)
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
# CONVERSIÓN DE FEATURES
# ============================================================

def preparar_features(
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

    return df


# ============================================================
# PREFLIGHT
# NO CONSULTA B
# ============================================================

def preflight():

    print()
    print("=" * 74)
    print("FASE 2.2 - PREFLIGHT TEST B")
    print("=" * 74)

    verificar_repo_limpio()

    config = cargar_config()

    commit_actual = (
        obtener_commit_actual()
    )

    if LOCK_PATH.exists():

        raise RuntimeError(
            "Existe el archivo de bloqueo "
            "del test B. No se puede continuar."
        )

    print()
    print(
        "[OK] Repositorio limpio."
    )

    print(
        "[OK] Configuración congelada válida."
    )

    print(
        "[OK] No existe bloqueo previo de B."
    )

    print(
        f"[OK] Commit pre-test congelado: "
        f"{PRETEST_COMMIT}"
    )

    print(
        f"[OK] Commit actual del código: "
        f"{commit_actual}"
    )

    print()
    print(
        f"Modelo : "
        f"{config['modelo']['clase']}"
    )

    print(
        f"Umbral : "
        f"{config['umbral']['valor']:.12f}"
    )

    print()
    print(
        "IMPORTANTE: este preflight "
        "NO consultó el corte B."
    )

    print()
    print("=" * 74)
    print("PREFLIGHT COMPLETADO")
    print("=" * 74)


# ============================================================
# CREAR LOCK ANTES DE CONSULTAR B
# ============================================================

def crear_lock(
    commit_actual,
):

    contenido = {
        "estado":
            "INICIADO",

        "fecha_inicio":
            datetime.now()
            .astimezone()
            .isoformat(),

        "pretest_commit":
            PRETEST_COMMIT,

        "evaluation_code_commit":
            commit_actual,

        "nota":
            (
                "El corte B solo puede "
                "evaluarse una vez."
            ),
    }

    with open(
        LOCK_PATH,
        "x",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            contenido,
            archivo,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# ACTUALIZAR LOCK
# ============================================================

def completar_lock(
    commit_actual,
    resultado,
):

    contenido = {
        "estado":
            "COMPLETADO",

        "fecha_evaluacion":
            resultado[
                "fecha_evaluacion"
            ],

        "pretest_commit":
            PRETEST_COMMIT,

        "evaluation_code_commit":
            commit_actual,

        "ap_b":
            resultado["ap_b"],

        "umbral":
            resultado["umbral"],

        "ganancia_b_q":
            resultado[
                "ganancia_b_q"
            ],
    }

    with open(
        LOCK_PATH,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            contenido,
            archivo,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# TEST ÚNICO B
# ============================================================

def evaluar_b():

    print()
    print("=" * 74)
    print("FASE 2.2 - ÚNICA EVALUACIÓN DEL CORTE B")
    print("=" * 74)

    # ----------------------------------------
    # Controles previos
    # ----------------------------------------

    verificar_repo_limpio()

    config = cargar_config()

    if LOCK_PATH.exists():

        raise RuntimeError(
            "EL TEST B YA FUE INICIADO "
            "O EJECUTADO.\n"
            "No se realizará una segunda "
            "evaluación."
        )

    commit_actual = (
        obtener_commit_actual()
    )

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
    print(
        f"Pre-test commit : "
        f"{PRETEST_COMMIT}"
    )

    print(
        f"Commit código   : "
        f"{commit_actual}"
    )

    print(
        f"Modelo          : "
        f"{config['modelo']['clase']}"
    )

    print(
        f"Umbral congelado: "
        f"{umbral:.12f}"
    )

    # ----------------------------------------
    # Primero cargamos A.
    # Aún no hemos tocado B.
    # ----------------------------------------

    print()
    print(
        "[1/5] Cargando corte A..."
    )

    df_a = cargar_corte(
        "A",
        features
    )

    df_a = preparar_features(
        df_a,
        features
    )

    if len(df_a) != FILAS_A_ESPERADAS:

        raise RuntimeError(
            "Cantidad inesperada "
            "de filas en A."
        )

    if (
        int(df_a["etiqueta"].sum())
        != POSITIVOS_A_ESPERADOS
    ):

        raise RuntimeError(
            "Cantidad inesperada "
            "de positivos en A."
        )

    print(
        f"[OK] A: {len(df_a):,} filas, "
        f"{df_a['etiqueta'].sum():,} positivos."
    )

    # ----------------------------------------
    # Crear bloqueo AHORA.
    # A partir de este punto B se considera
    # consumido aunque hubiese un fallo.
    # ----------------------------------------

    crear_lock(
        commit_actual
    )

    print()
    print(
        "[2/5] Bloqueo creado."
    )

    print(
        "      A partir de este punto "
        "el test B se considera consumido."
    )

    # ----------------------------------------
    # ÚNICA LECTURA / EVALUACIÓN DE B
    # ----------------------------------------

    print()
    print(
        "[3/5] Cargando corte B "
        "por única vez..."
    )

    df_b = cargar_corte(
        "B",
        features
    )

    df_b = preparar_features(
        df_b,
        features
    )

    if len(df_b) != FILAS_B_ESPERADAS:

        raise RuntimeError(
            "Cantidad inesperada "
            "de filas en B."
        )

    print(
        f"[OK] B: {len(df_b):,} filas."
    )

    # ----------------------------------------
    # Entrenar FINAL únicamente con A
    # ----------------------------------------

    print()
    print(
        "[4/5] Entrenando modelo final "
        "con todo A..."
    )

    pipeline = crear_pipeline(
        config
    )

    inicio_train = perf_counter()

    pipeline.fit(
        df_a[features],
        df_a["etiqueta"]
    )

    tiempo_train = (
        perf_counter()
        - inicio_train
    )

    print(
        f"[OK] Entrenamiento: "
        f"{tiempo_train:.2f} s"
    )

    # ----------------------------------------
    # Evaluar B UNA VEZ
    # ----------------------------------------

    print()
    print(
        "[5/5] Calculando métricas "
        "finales en B..."
    )

    inicio_pred = perf_counter()

    probabilidades = (
        pipeline
        .predict_proba(
            df_b[features]
        )[:, 1]
    )

    tiempo_pred = (
        perf_counter()
        - inicio_pred
    )

    y_b = (
        df_b[
            "etiqueta"
        ]
        .to_numpy()
    )

    predicciones = (
        probabilidades
        >= umbral
    ).astype(int)

    ap_b = (
        average_precision_score(
            y_b,
            probabilidades
        )
    )

    precision_b = (
        precision_score(
            y_b,
            predicciones,
            zero_division=0
        )
    )

    recall_b = (
        recall_score(
            y_b,
            predicciones,
            zero_division=0
        )
    )

    cm = confusion_matrix(
        y_b,
        predicciones,
        labels=[
            0,
            1
        ],
    )

    tn, fp, fn, tp = (
        cm.ravel()
    )

    contactados = int(
        tp + fp
    )

    costo_total = (
        contactados
        * 5.0
    )

    retenidos_esperados = (
        tp
        * 0.25
    )

    beneficio_esperado = (
        tp
        * 15.0
    )

    ganancia_b = (
        beneficio_esperado
        - costo_total
    )

    fecha = (
        datetime.now()
        .astimezone()
        .isoformat()
    )

    resultado = {
        "fecha_evaluacion":
            fecha,

        "pretest_commit":
            PRETEST_COMMIT,

        "evaluation_code_commit":
            commit_actual,

        "modelo":
            config[
                "modelo"
            ][
                "clase"
            ],

        "filas_b":
            int(
                len(df_b)
            ),

        "positivos_b":
            int(
                df_b[
                    "etiqueta"
                ].sum()
            ),

        "tasa_positiva_b":
            float(
                df_b[
                    "etiqueta"
                ].mean()
            ),

        "ap_cv_a":
            float(
                config[
                    "metrica_seleccion"
                ][
                    "ap_validacion_media"
                ]
            ),

        "ap_b":
            float(ap_b),

        "diferencia_ap_b_vs_cv":
            float(
                ap_b
                - config[
                    "metrica_seleccion"
                ][
                    "ap_validacion_media"
                ]
            ),

        "umbral":
            umbral,

        "contactados":
            contactados,

        "tp":
            int(tp),

        "fp":
            int(fp),

        "tn":
            int(tn),

        "fn":
            int(fn),

        "precision":
            float(
                precision_b
            ),

        "recall":
            float(
                recall_b
            ),

        "retenidos_esperados":
            float(
                retenidos_esperados
            ),

        "costo_total_q":
            float(
                costo_total
            ),

        "beneficio_esperado_q":
            float(
                beneficio_esperado
            ),

        "ganancia_b_q":
            float(
                ganancia_b
            ),

        "segundos_entrenamiento":
            float(
                tiempo_train
            ),

        "segundos_prediccion":
            float(
                tiempo_pred
            ),
    }

    # ----------------------------------------
    # Guardar resumen
    # ----------------------------------------

    pd.DataFrame(
        [resultado]
    ).to_csv(
        RESULTADO_PATH,
        index=False
    )

    # ----------------------------------------
    # Guardar matriz
    # ----------------------------------------

    matriz_df = pd.DataFrame(
        cm,
        index=[
            "Real_0",
            "Real_1",
        ],
        columns=[
            "Pred_0",
            "Pred_1",
        ],
    )

    matriz_df.to_csv(
        MATRIZ_PATH
    )

    # ----------------------------------------
    # Gráfica matriz de confusión
    # ----------------------------------------

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=[
            "No abandono",
            "Abandono",
        ],
    )

    display.plot(
        values_format="d"
    )

    plt.title(
        "Matriz de confusión - Test B"
    )

    plt.tight_layout()

    plt.savefig(
        MATRIZ_PNG_PATH,
        dpi=160,
        bbox_inches="tight"
    )

    plt.close()

    # ----------------------------------------
    # Bitácora
    # ----------------------------------------

    texto = f"""# Fase 2.2 - Única evaluación del corte B

## Registro

- Fecha de evaluación: {fecha}
- Commit de congelamiento pre-test: `{PRETEST_COMMIT}`
- Commit del código de evaluación: `{commit_actual}`
- Modelo: {resultado["modelo"]}
- Umbral congelado: {umbral:.12f}

## Resultados de validación A

- Average Precision CV A: {resultado["ap_cv_a"]:.6f}

## Resultados del test B

- Población B: {resultado["filas_b"]:,}
- Positivos B: {resultado["positivos_b"]:,}
- Tasa positiva B: {resultado["tasa_positiva_b"]:.4f}
- Average Precision B: {resultado["ap_b"]:.6f}
- Diferencia AP B - CV A: {resultado["diferencia_ap_b_vs_cv"]:.6f}

## Decisión con umbral congelado

- Umbral: {umbral:.6f}
- Contactados: {resultado["contactados"]:,}
- TP: {resultado["tp"]:,}
- FP: {resultado["fp"]:,}
- TN: {resultado["tn"]:,}
- FN: {resultado["fn"]:,}
- Precision: {resultado["precision"]:.4f}
- Recall: {resultado["recall"]:.4f}

## Resultado económico

- Retenidos esperados: {resultado["retenidos_esperados"]:.2f}
- Costo total: Q{resultado["costo_total_q"]:,.2f}
- Beneficio esperado: Q{resultado["beneficio_esperado_q"]:,.2f}
- Ganancia esperada en B: Q{resultado["ganancia_b_q"]:,.2f}

## Regla posterior al test

El corte B fue utilizado una única vez. No se modificarán el modelo,
las features, los hiperparámetros ni el umbral después de observar
este resultado.
"""

    BITACORA_PATH.write_text(
        texto,
        encoding="utf-8"
    )

    # ----------------------------------------
    # Completar lock
    # ----------------------------------------

    completar_lock(
        commit_actual,
        resultado
    )

    # ----------------------------------------
    # SALIDA
    # ----------------------------------------

    print()
    print("=" * 74)
    print("RESULTADO ÚNICO DEL TEST B")
    print("=" * 74)

    print(
        f"Fecha                 : "
        f"{fecha}"
    )

    print(
        f"Pre-test commit       : "
        f"{PRETEST_COMMIT}"
    )

    print(
        f"Commit evaluación     : "
        f"{commit_actual}"
    )

    print()
    print(
        f"Población B           : "
        f"{len(df_b):,}"
    )

    print(
        f"Positivos B           : "
        f"{int(df_b['etiqueta'].sum()):,}"
    )

    print(
        f"Tasa positiva B       : "
        f"{df_b['etiqueta'].mean():.4f}"
    )

    print()
    print(
        f"AP CV corte A         : "
        f"{resultado['ap_cv_a']:.6f}"
    )

    print(
        f"AP test B             : "
        f"{ap_b:.6f}"
    )

    print(
        f"Diferencia B - CV     : "
        f"{resultado['diferencia_ap_b_vs_cv']:.6f}"
    )

    print()
    print(
        f"Umbral congelado      : "
        f"{umbral:.6f}"
    )

    print(
        f"Contactados           : "
        f"{contactados:,}"
    )

    print(
        f"Precision             : "
        f"{precision_b:.4f}"
    )

    print(
        f"Recall                : "
        f"{recall_b:.4f}"
    )

    print()
    print("MATRIZ DE CONFUSIÓN")
    print("-" * 74)

    print(
        f"TN: {tn:,}    "
        f"FP: {fp:,}"
    )

    print(
        f"FN: {fn:,}    "
        f"TP: {tp:,}"
    )

    print()
    print("RESULTADO ECONÓMICO")
    print("-" * 74)

    print(
        f"Retenidos esperados   : "
        f"{retenidos_esperados:,.2f}"
    )

    print(
        f"Costo total           : "
        f"Q{costo_total:,.2f}"
    )

    print(
        f"Beneficio esperado    : "
        f"Q{beneficio_esperado:,.2f}"
    )

    print(
        f"GANANCIA B            : "
        f"Q{ganancia_b:,.2f}"
    )

    print()
    print(
        f"Tiempo entrenamiento  : "
        f"{tiempo_train:.2f} s"
    )

    print(
        f"Tiempo predicción     : "
        f"{tiempo_pred:.2f} s"
    )

    print()
    print("=" * 74)
    print("TEST B CONSUMIDO")
    print("=" * 74)

    print(
        "[OK] Esta fue la única "
        "evaluación del corte B."
    )

    print(
        "[OK] No ajustar modelo ni "
        "umbral después de este punto."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Valida el estado sin "
            "consultar el corte B."
        ),
    )

    args = parser.parse_args()

    if args.preflight:

        preflight()

    else:

        evaluar_b()


if __name__ == "__main__":
    main()