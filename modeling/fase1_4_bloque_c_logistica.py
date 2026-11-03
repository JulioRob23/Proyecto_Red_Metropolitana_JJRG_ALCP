from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

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

BASELINES_PATH = (
    OUTPUT_DIR
    / "fase1_4_baselines_resultados.csv"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RANDOM_STATE = 42
MAX_ITER = 3000

LAMBDAS = [
    0.01,
    0.1,
    1.0,
    10.0,
    100.0,
]

PENALIZACIONES = [
    "l1",
    "l2",
]


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
# POSTGRES
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
            for columna
            in cursor.description
        ]

        datos = pd.DataFrame(
            filas,
            columns=nombres
        )

    finally:
        conexion.close()

    return datos


# ============================================================
# PREPARAR DATOS + FOLDS
# ============================================================

def preparar_datos():

    if not FOLDS_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase1_4_folds.csv"
        )

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

    if len(df) != 59999:

        raise RuntimeError(
            "El corte A debe contener "
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

    # ----------------------------------------
    # Convertir numéricas explícitamente
    # ----------------------------------------

    for columna in FEATURES_NUMERICAS:

        if columna == "es_multimodal":

            df[columna] = (
                df[columna]
                .map({
                    True: 1.0,
                    False: 0.0,
                    1: 1.0,
                    0: 0.0,
                })
            )

        else:

            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            )

    # ----------------------------------------
    # Preparar categóricas
    # ----------------------------------------

    for columna in FEATURES_CATEGORICAS:

        df[columna] = (
            df[columna]
            .where(
                df[columna].notna(),
                np.nan
            )
            .astype("object")
        )

    return df


# ============================================================
# ONE HOT COMPATIBLE
# ============================================================

def crear_one_hot_encoder():

    try:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )

    except TypeError:

        # Compatibilidad con versiones
        # anteriores de scikit-learn.
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=True,
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
                crear_one_hot_encoder(),
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
# CREAR REGRESIÓN LOGÍSTICA
# Compatible con scikit-learn >= 1.8
# ============================================================

def crear_logistica(
    penalizacion,
    C,
):

    if penalizacion.lower() == "l1":
        l1_ratio = 1.0

    elif penalizacion.lower() == "l2":
        l1_ratio = 0.0

    else:
        raise ValueError(
            "Penalización no válida. "
            "Use l1 o l2."
        )

    return LogisticRegression(
        C=C,
        l1_ratio=l1_ratio,
        solver="liblinear",
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
    )

# ============================================================
# GRID L1 / L2
# ============================================================

def ejecutar_grid(df):

    resultados = []

    folds = sorted(
        df["fold"].unique()
    )

    total_modelos = (
        len(folds)
        * len(PENALIZACIONES)
        * len(LAMBDAS)
    )

    contador = 0

    inicio_total = perf_counter()

    for fold in folds:

        print()
        print("=" * 70)
        print(
            f"PREPARANDO FOLD {fold}"
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

        X_validacion = validacion[
            FEATURES
        ]

        y_validacion = (
            validacion["etiqueta"]
            .to_numpy()
        )

        # El preprocesamiento se aprende
        # solamente con training del fold.
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
                X_validacion
            )
        )

        tiempo_pre = (
            perf_counter()
            - inicio_pre
        )

        print(
            "[OK] Preprocesamiento "
            f"fold {fold}: "
            f"{tiempo_pre:.2f} s"
        )

        for penalizacion in PENALIZACIONES:

            for lambda_ in LAMBDAS:

                contador += 1

                C = (
                    1.0
                    / lambda_
                )

                print(
                    f"[{contador:02d}/"
                    f"{total_modelos}] "
                    f"fold={fold} "
                    f"penalty={penalizacion.upper()} "
                    f"lambda={lambda_:g} "
                    f"C={C:g}"
                )

                modelo = crear_logistica(
                    penalizacion=penalizacion,
                    C=C,
                )

                inicio = perf_counter()

                modelo.fit(
                    X_train_proc,
                    y_train,
                )

                probabilidades = (
                    modelo
                    .predict_proba(
                        X_val_proc
                    )[:, 1]
                )

                ap = (
                    average_precision_score(
                        y_validacion,
                        probabilidades,
                    )
                )

                duracion = (
                    perf_counter()
                    - inicio
                )

                iteraciones = int(
                    modelo.n_iter_[0]
                )

                resultados.append({
                    "penalizacion":
                        penalizacion.upper(),
                    "lambda":
                        lambda_,
                    "C":
                        C,
                    "fold":
                        int(fold),
                    "average_precision":
                        float(ap),
                    "iteraciones":
                        iteraciones,
                    "segundos":
                        round(
                            duracion,
                            4
                        ),
                })

                print(
                    "      "
                    f"AP={ap:.6f} | "
                    f"iter={iteraciones} | "
                    f"{duracion:.2f}s"
                )

    duracion_total = (
        perf_counter()
        - inicio_total
    )

    print()
    print(
        "[OK] Grid completo en "
        f"{duracion_total:.2f} s"
    )

    return (
        pd.DataFrame(
            resultados
        ),
        duracion_total,
    )


# ============================================================
# RESUMEN POR λ
# ============================================================

def resumir_grid(detalle):

    resumen = (
        detalle
        .groupby(
            [
                "penalizacion",
                "lambda",
                "C",
            ],
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
            tiempo_medio_s=(
                "segundos",
                "mean"
            ),
        )
    )

    resumen[
        "ap_media"
    ] = resumen[
        "ap_media"
    ].round(6)

    resumen[
        "ap_std"
    ] = resumen[
        "ap_std"
    ].round(6)

    resumen[
        "tiempo_medio_s"
    ] = resumen[
        "tiempo_medio_s"
    ].round(4)

    return resumen


# ============================================================
# ELEGIR MEJOR λ POR PENALIZACIÓN
# ============================================================

def elegir_mejores(resumen):

    mejores = []

    for penalizacion in [
        "L1",
        "L2",
    ]:

        candidatos = (
            resumen[
                resumen[
                    "penalizacion"
                ]
                == penalizacion
            ]
            .sort_values(
                by=[
                    "ap_media",
                    "ap_std",
                    "lambda",
                ],
                ascending=[
                    False,
                    True,
                    True,
                ],
            )
        )

        mejor = (
            candidatos
            .iloc[0]
            .to_dict()
        )

        mejores.append(
            mejor
        )

    return pd.DataFrame(
        mejores
    )


# ============================================================
# TABLA FINAL DE 1.4
# ============================================================

def crear_tabla_modelos(
    mejores
):

    if not BASELINES_PATH.exists():

        raise FileNotFoundError(
            "No se encontró el resultado "
            "del Bloque B."
        )

    baselines = pd.read_csv(
        BASELINES_PATH
    )

    filas = []

    for _, fila in (
        baselines.iterrows()
    ):

        if (
            fila["modelo"]
            == "Baseline prevalencia"
        ):

            configuracion = (
                "p = 8310 / 59999"
            )

        else:

            configuracion = (
                "dias_desde_ultimo_viaje"
            )

        filas.append({
            "modelo":
                fila["modelo"],
            "configuracion":
                configuracion,
            "ap_media":
                fila["ap_media"],
            "ap_std":
                fila["ap_std"],
        })

    for _, fila in (
        mejores.iterrows()
    ):

        penalizacion = (
            fila["penalizacion"]
        )

        filas.append({
            "modelo":
                f"Logística {penalizacion}",
            "configuracion":
                (
                    f"lambda="
                    f"{fila['lambda']:g}; "
                    f"C={fila['C']:g}"
                ),
            "ap_media":
                fila["ap_media"],
            "ap_std":
                fila["ap_std"],
        })

    tabla = pd.DataFrame(
        filas
    )

    return (
        tabla
        .sort_values(
            "ap_media",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# GRÁFICA AP VS λ
# ============================================================

def crear_grafica(
    resumen,
    mejores
):

    figura = plt.figure(
        figsize=(9, 6)
    )

    for penalizacion in [
        "L1",
        "L2",
    ]:

        datos = (
            resumen[
                resumen[
                    "penalizacion"
                ]
                == penalizacion
            ]
            .sort_values(
                "lambda"
            )
        )

        plt.errorbar(
            datos["lambda"],
            datos["ap_media"],
            yerr=datos["ap_std"],
            marker="o",
            capsize=3,
            label=(
                f"Logística {penalizacion}"
            ),
        )

        mejor = (
            mejores[
                mejores[
                    "penalizacion"
                ]
                == penalizacion
            ]
            .iloc[0]
        )

        plt.annotate(
            (
                f"{penalizacion}: "
                f"λ={mejor['lambda']:g}"
            ),
            xy=(
                mejor["lambda"],
                mejor["ap_media"],
            ),
            xytext=(
                8,
                8,
            ),
            textcoords="offset points",
        )

    plt.xscale(
        "log"
    )

    plt.xlabel(
        "λ (fuerza de regularización)"
    )

    plt.ylabel(
        "Average Precision"
    )

    plt.title(
        "Validación cruzada: "
        "Average Precision vs λ"
    )

    plt.legend()

    plt.grid(
        True,
        alpha=0.25
    )

    plt.tight_layout()

    ruta = (
        OUTPUT_DIR
        / "fase1_4_ap_vs_lambda.png"
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
# OOF DE LOS MEJORES L1 Y L2
# ============================================================

def generar_oof_mejores(
    df,
    mejores
):

    resultados = []

    for fold in sorted(
        df["fold"].unique()
    ):

        print()
        print(
            "[OOF] "
            f"Fold {fold}"
        )

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

        X_validacion = (
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

        for _, mejor in (
            mejores.iterrows()
        ):

            penalizacion = (
                mejor[
                    "penalizacion"
                ]
                .lower()
            )

            modelo = crear_logistica(
                penalizacion=penalizacion,
                C=float(
                    mejor["C"]
                ),
            )

            modelo.fit(
                X_train,
                y_train
            )

            probabilidades = (
                modelo
                .predict_proba(
                    X_validacion
                )[:, 1]
            )

            for (
                unidad_id,
                etiqueta,
                probabilidad,
            ) in zip(
                validacion[
                    "unidad_id"
                ],
                validacion[
                    "etiqueta"
                ],
                probabilidades,
            ):

                resultados.append({
                    "unidad_id":
                        unidad_id,
                    "fold":
                        int(fold),
                    "etiqueta":
                        int(etiqueta),
                    "modelo":
                        (
                            "Logística "
                            + mejor[
                                "penalizacion"
                            ]
                        ),
                    "lambda":
                        float(
                            mejor["lambda"]
                        ),
                    "probabilidad":
                        float(
                            probabilidad
                        ),
                })

    return pd.DataFrame(
        resultados
    )


# ============================================================
# COEFICIENTES DEL MEJOR MODELO
# ============================================================

def entrenar_para_coeficientes(
    df,
    mejores
):

    mejor_global = (
        mejores
        .sort_values(
            by=[
                "ap_media",
                "ap_std",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .iloc[0]
    )

    penalizacion = (
        mejor_global[
            "penalizacion"
        ]
        .lower()
    )

    lambda_ = float(
        mejor_global[
            "lambda"
        ]
    )

    C = float(
        mejor_global[
            "C"
        ]
    )

    preprocesador = (
        crear_preprocesador()
    )

    X = preprocesador.fit_transform(
        df[FEATURES]
    )

    y = (
        df[
            "etiqueta"
        ]
        .to_numpy()
    )

    modelo = crear_logistica(
        penalizacion=penalizacion,
        C=C,
    )

    modelo.fit(
        X,
        y
    )

    nombres = (
        preprocesador
        .get_feature_names_out()
    )

    nombres_limpios = []

    for nombre in nombres:

        nombre = (
            nombre
            .replace(
                "num__",
                ""
            )
            .replace(
                "cat__",
                ""
            )
        )

        nombres_limpios.append(
            nombre
        )

    coeficientes = pd.DataFrame({
        "feature":
            nombres_limpios,
        "coeficiente":
            modelo.coef_[0],
    })

    coeficientes[
        "coeficiente"
    ] = (
        coeficientes[
            "coeficiente"
        ]
        .round(6)
    )

    coeficientes = (
        coeficientes
        .sort_values(
            "coeficiente",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    top5 = (
        coeficientes[
            coeficientes[
                "coeficiente"
            ] > 0
        ]
        .head(5)
        .copy()
    )

    return (
        mejor_global,
        coeficientes,
        top5,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 1.4 - BLOQUE C")
    print("REGRESIÓN LOGÍSTICA REGULARIZADA")
    print("=" * 70)

    df = preparar_datos()

    print()
    print(
        f"Filas corte A : {len(df):,}"
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
        "Penalizaciones: L1, L2"
    )

    print(
        f"Lambdas       : {LAMBDAS}"
    )

    # ----------------------------------------
    # GRID
    # ----------------------------------------

    detalle, duracion_total = (
        ejecutar_grid(
            df
        )
    )

    resumen = resumir_grid(
        detalle
    )

    mejores = elegir_mejores(
        resumen
    )

    tabla_modelos = (
        crear_tabla_modelos(
            mejores
        )
    )

    # ----------------------------------------
    # GUARDAR GRID
    # ----------------------------------------

    ruta_detalle = (
        OUTPUT_DIR
        / "fase1_4_lambda_por_fold.csv"
    )

    ruta_resumen = (
        OUTPUT_DIR
        / "fase1_4_lambda_resultados.csv"
    )

    ruta_mejores = (
        OUTPUT_DIR
        / "fase1_4_lambda_mejores.csv"
    )

    ruta_modelos = (
        OUTPUT_DIR
        / "fase1_4_resultados_modelos.csv"
    )

    detalle.to_csv(
        ruta_detalle,
        index=False
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    mejores.to_csv(
        ruta_mejores,
        index=False
    )

    tabla_modelos.to_csv(
        ruta_modelos,
        index=False
    )

    # ----------------------------------------
    # GRÁFICA
    # ----------------------------------------

    ruta_grafica = crear_grafica(
        resumen,
        mejores
    )

    # ----------------------------------------
    # OOF
    # ----------------------------------------

    oof = generar_oof_mejores(
        df,
        mejores
    )

    ruta_oof = (
        OUTPUT_DIR
        / "fase1_4_logisticas_oof.csv"
    )

    oof.to_csv(
        ruta_oof,
        index=False
    )

    # ----------------------------------------
    # COEFICIENTES
    # ----------------------------------------

    (
        mejor_global,
        coeficientes,
        top5,
    ) = entrenar_para_coeficientes(
        df,
        mejores
    )

    ruta_coeficientes = (
        OUTPUT_DIR
        / "fase1_4_coeficientes.csv"
    )

    ruta_top5 = (
        OUTPUT_DIR
        / "fase1_4_top5_coeficientes.csv"
    )

    coeficientes.to_csv(
        ruta_coeficientes,
        index=False
    )

    top5.to_csv(
        ruta_top5,
        index=False
    )

    # ----------------------------------------
    # RESULTADOS
    # ----------------------------------------

    print()
    print("=" * 70)
    print("RESULTADOS POR λ")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("MEJOR λ POR PENALIZACIÓN")
    print("=" * 70)

    print(
        mejores.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("COMPARACIÓN FINAL DE MODELOS")
    print("=" * 70)

    print(
        tabla_modelos.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("MEJOR LOGÍSTICA")
    print("=" * 70)

    print(
        f"Penalización : "
        f"{mejor_global['penalizacion']}"
    )

    print(
        f"lambda       : "
        f"{mejor_global['lambda']:g}"
    )

    print(
        f"C            : "
        f"{mejor_global['C']:g}"
    )

    print(
        f"AP media     : "
        f"{mejor_global['ap_media']:.6f}"
    )

    print(
        f"AP std       : "
        f"{mejor_global['ap_std']:.6f}"
    )

    print()
    print("=" * 70)
    print(
        "TOP 5 COEFICIENTES POSITIVOS"
    )
    print("=" * 70)

    print(
        top5.to_string(
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
        ruta_mejores,
        ruta_modelos,
        ruta_grafica,
        ruta_oof,
        ruta_coeficientes,
        ruta_top5,
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
    print(
        f"Tiempo grid: "
        f"{duracion_total:.2f} s"
    )

    print()
    print("=" * 70)
    print("BLOQUE C COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()