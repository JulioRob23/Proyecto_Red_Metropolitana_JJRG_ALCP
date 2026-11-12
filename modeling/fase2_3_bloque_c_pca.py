from pathlib import Path
from time import perf_counter
import os

import numpy as np
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


# ============================================================
# RECURSOS
# ============================================================

os.environ.setdefault(
    "OMP_NUM_THREADS",
    "1"
)


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


# ============================================================
# CONFIGURACIÓN
# ============================================================

RANDOM_STATE = 42

K_FINAL = 5

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310


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

def cargar_corte_a():

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

def preparar_datos(
    df
):

    df = df.copy()

    if len(df) != FILAS_ESPERADAS:

        raise RuntimeError(
            f"Se esperaban "
            f"{FILAS_ESPERADAS:,} filas."
        )

    if (
        df["unidad_id"]
        .duplicated()
        .sum()
        != 0
    ):

        raise RuntimeError(
            "Hay unidades duplicadas."
        )

    df["etiqueta"] = (
        df["etiqueta"]
        .astype(int)
    )

    if int(
        df["etiqueta"].sum()
    ) != POSITIVOS_ESPERADOS:

        raise RuntimeError(
            "Cantidad incorrecta "
            "de positivos."
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
            "Hay valores nulos."
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
# PREPROCESAMIENTO
# ============================================================

def crear_preprocesador():

    numericas = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categoricas = Pipeline(
        steps=[
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
# PCA + KMEANS
# ============================================================

def ejecutar_segmentacion(
    df
):

    preprocesador = (
        crear_preprocesador()
    )

    print()
    print(
        "[1/4] Transformando features..."
    )

    inicio = perf_counter()

    X = (
        preprocesador
        .fit_transform(
            df[FEATURES]
        )
    )

    print(
        f"[OK] Matriz transformada: "
        f"{X.shape[0]:,} x "
        f"{X.shape[1]}"
    )

    print(
        f"[OK] Tiempo: "
        f"{perf_counter() - inicio:.2f} s"
    )

    # ----------------------------------------
    # KMeans definitivo
    # ----------------------------------------

    print()
    print(
        "[2/4] Entrenando KMeans "
        f"definitivo con k={K_FINAL}..."
    )

    kmeans = KMeans(
        n_clusters=K_FINAL,
        init="k-means++",
        n_init=10,
        max_iter=300,
        random_state=RANDOM_STATE,
        algorithm="lloyd",
    )

    inicio = perf_counter()

    segmentos = (
        kmeans
        .fit_predict(
            X
        )
    )

    print(
        f"[OK] KMeans: "
        f"{perf_counter() - inicio:.2f} s"
    )

    # Usaremos segmentos 1...5
    # para que sea más fácil presentarlos.
    segmentos_presentacion = (
        segmentos
        + 1
    )

    # ----------------------------------------
    # PCA
    # ----------------------------------------

    print()
    print(
        "[3/4] Calculando PCA "
        "a dos componentes..."
    )

    pca = PCA(
        n_components=2,
        svd_solver="randomized",
        random_state=RANDOM_STATE,
    )

    inicio = perf_counter()

    X_pca = (
        pca
        .fit_transform(
            X
        )
    )

    print(
        f"[OK] PCA: "
        f"{perf_counter() - inicio:.2f} s"
    )

    return (
        X,
        segmentos_presentacion,
        X_pca,
        pca,
        kmeans,
    )


# ============================================================
# RESUMEN DE SEGMENTOS
# ============================================================

def crear_resumen_segmentos(
    df,
    segmentos
):

    resultado = pd.DataFrame({
        "unidad_id":
            df["unidad_id"].values,

        "segmento":
            segmentos,

        "etiqueta":
            df["etiqueta"].values,
    })

    resumen = (
        resultado
        .groupby(
            "segmento",
            as_index=False
        )
        .agg(
            tamanio=(
                "unidad_id",
                "count"
            ),
            positivos=(
                "etiqueta",
                "sum"
            ),
        )
    )

    resumen[
        "proporcion_poblacion"
    ] = (
        resumen["tamanio"]
        / len(resultado)
    )

    resumen[
        "tasa_abandono"
    ] = (
        resumen["positivos"]
        / resumen["tamanio"]
    )

    return (
        resultado,
        resumen,
    )


# ============================================================
# GRÁFICA PCA
# ============================================================

def crear_grafica_pca(
    resultados,
    pca,
):

    figura = plt.figure(
        figsize=(10, 7)
    )

    for segmento in sorted(
        resultados[
            "segmento"
        ].unique()
    ):

        datos = (
            resultados[
                resultados[
                    "segmento"
                ]
                == segmento
            ]
        )

        plt.scatter(
            datos["PC1"],
            datos["PC2"],
            s=8,
            alpha=0.35,
            label=(
                f"Segmento {segmento}"
            ),
        )

    var1 = (
        pca
        .explained_variance_ratio_[0]
        * 100
    )

    var2 = (
        pca
        .explained_variance_ratio_[1]
        * 100
    )

    plt.xlabel(
        f"PC1 ({var1:.2f}% varianza)"
    )

    plt.ylabel(
        f"PC2 ({var2:.2f}% varianza)"
    )

    plt.title(
        "Segmentos de usuarios "
        "proyectados con PCA"
    )

    plt.legend(
        markerscale=2
    )

    plt.grid(
        True,
        alpha=0.20
    )

    plt.tight_layout()

    ruta = (
        FASE2_DIR
        / "fase2_3_pca_segmentos.png"
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
    print("=" * 72)
    print("FASE 2.3 - BLOQUE C")
    print("KMEANS DEFINITIVO Y PCA")
    print("=" * 72)

    print()
    print(
        f"k seleccionado : {K_FINAL}"
    )

    print(
        "Justificación  : "
        "mejor silhouette y codo "
        "alrededor de 5 clusters"
    )

    df = cargar_corte_a()

    df = preparar_datos(
        df
    )

    (
        X,
        segmentos,
        X_pca,
        pca,
        kmeans,
    ) = ejecutar_segmentacion(
        df
    )

    # ----------------------------------------
    # Crear resultados completos
    # ----------------------------------------

    resultados = df[
        [
            "unidad_id",
            "etiqueta",
        ]
    ].copy()

    resultados[
        "segmento"
    ] = segmentos

    resultados[
        "PC1"
    ] = X_pca[:, 0]

    resultados[
        "PC2"
    ] = X_pca[:, 1]

    # ----------------------------------------
    # Resumen segmentos
    # ----------------------------------------

    _, resumen_segmentos = (
        crear_resumen_segmentos(
            df,
            segmentos
        )
    )

    # ----------------------------------------
    # Varianza explicada
    # ----------------------------------------

    varianza = pd.DataFrame([
        {
            "componente":
                "PC1",
            "varianza_explicada":
                pca
                .explained_variance_ratio_[0],
        },
        {
            "componente":
                "PC2",
            "varianza_explicada":
                pca
                .explained_variance_ratio_[1],
        },
    ])

    varianza_total = float(
        pca
        .explained_variance_ratio_
        .sum()
    )

    # ----------------------------------------
    # Guardar
    # ----------------------------------------

    ruta_asignaciones = (
        FASE2_DIR
        / "fase2_3_segmentos_pca.csv"
    )

    ruta_resumen = (
        FASE2_DIR
        / "fase2_3_segmentos_resumen_inicial.csv"
    )

    ruta_varianza = (
        FASE2_DIR
        / "fase2_3_pca_varianza.csv"
    )

    resultados.to_csv(
        ruta_asignaciones,
        index=False
    )

    resumen_segmentos.to_csv(
        ruta_resumen,
        index=False
    )

    varianza.to_csv(
        ruta_varianza,
        index=False
    )

    ruta_grafica = (
        crear_grafica_pca(
            resultados,
            pca,
        )
    )

    # ----------------------------------------
    # SALIDAS
    # ----------------------------------------

    print()
    print("=" * 72)
    print("VARIANZA EXPLICADA PCA")
    print("=" * 72)

    print(
        f"PC1             : "
        f"{pca.explained_variance_ratio_[0]:.6f} "
        f"("
        f"{pca.explained_variance_ratio_[0] * 100:.2f}%"
        f")"
    )

    print(
        f"PC2             : "
        f"{pca.explained_variance_ratio_[1]:.6f} "
        f"("
        f"{pca.explained_variance_ratio_[1] * 100:.2f}%"
        f")"
    )

    print(
        f"Varianza total  : "
        f"{varianza_total:.6f} "
        f"({varianza_total * 100:.2f}%)"
    )

    print()
    print("=" * 72)
    print("TAMAÑO Y ABANDONO POR SEGMENTO")
    print("=" * 72)

    print(
        resumen_segmentos
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 72)
    print("ARCHIVOS GENERADOS")
    print("=" * 72)

    for ruta in [
        ruta_asignaciones,
        ruta_resumen,
        ruta_varianza,
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
    print("=" * 72)
    print("BLOQUE C COMPLETADO")
    print("=" * 72)

    print(
        "[OK] KMeans definitivo: k=5."
    )

    print(
        "[OK] PCA calculado sobre "
        "features transformadas."
    )

    print(
        "[OK] La etiqueta no participó "
        "en la formación de segmentos."
    )


if __name__ == "__main__":
    main()