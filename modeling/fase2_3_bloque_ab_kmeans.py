from pathlib import Path
from time import perf_counter
import os

import numpy as np
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


# ============================================================
# CONTROL DE RECURSOS
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

FASE2_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONTROLES
# ============================================================

RANDOM_STATE = 42

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310

K_CANDIDATOS = [
    2,
    3,
    4,
    5,
    6,
    7,
    8,
]

SILHOUETTE_SAMPLE_SIZE = 10000


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

    if not ENV_PATH.exists():

        raise FileNotFoundError(
            "No se encontró el archivo .env"
        )

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
        port=int(
            env["POSTGRES_PORT"]
        ),
    )


# ============================================================
# CARGAR EXCLUSIVAMENTE CORTE A
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
# PREPARAR TIPOS
# ============================================================

def preparar_datos(
    df
):

    df = df.copy()

    if len(df) != FILAS_ESPERADAS:

        raise RuntimeError(
            f"Se esperaban "
            f"{FILAS_ESPERADAS:,} filas "
            f"y llegaron {len(df):,}."
        )

    df["etiqueta"] = (
        df["etiqueta"]
        .astype(int)
    )

    if (
        int(df["etiqueta"].sum())
        != POSITIVOS_ESPERADOS
    ):

        raise RuntimeError(
            "La cantidad de positivos "
            "no coincide con corte A."
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

    # ----------------------------------------
    # Numéricas
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

    nulos = int(
        df[FEATURES]
        .isna()
        .sum()
        .sum()
    )

    if nulos != 0:

        raise RuntimeError(
            f"Se encontraron {nulos} "
            "valores nulos."
        )

    return df


# ============================================================
# ONE HOT COMPATIBLE
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
# PREPROCESAMIENTO PARA CLUSTERING
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
# TRANSFORMAR
# ============================================================

def transformar_features(
    df
):

    preprocesador = (
        crear_preprocesador()
    )

    inicio = perf_counter()

    X = (
        preprocesador
        .fit_transform(
            df[FEATURES]
        )
    )

    duracion = (
        perf_counter()
        - inicio
    )

    nombres = (
        preprocesador
        .get_feature_names_out()
    )

    nombres = [
        nombre
        .replace(
            "num__",
            ""
        )
        .replace(
            "cat__",
            ""
        )
        for nombre in nombres
    ]

    return (
        X,
        nombres,
        duracion,
    )


# ============================================================
# PROBAR K
# ============================================================

def evaluar_k(
    X
):

    resultados = []

    for k in K_CANDIDATOS:

        print()
        print("=" * 70)
        print(
            f"K = {k}"
        )
        print("=" * 70)

        modelo = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=RANDOM_STATE,
            algorithm="lloyd",
        )

        inicio_fit = perf_counter()

        etiquetas = (
            modelo
            .fit_predict(
                X
            )
        )

        tiempo_fit = (
            perf_counter()
            - inicio_fit
        )

        print(
            f"[OK] KMeans: "
            f"{tiempo_fit:.2f} s"
        )

        print(
            "[...] Calculando silhouette "
            f"con muestra de "
            f"{SILHOUETTE_SAMPLE_SIZE:,}..."
        )

        inicio_silhouette = (
            perf_counter()
        )

        silhouette = (
            silhouette_score(
                X,
                etiquetas,
                metric="euclidean",
                sample_size=(
                    SILHOUETTE_SAMPLE_SIZE
                ),
                random_state=RANDOM_STATE,
            )
        )

        tiempo_silhouette = (
            perf_counter()
            - inicio_silhouette
        )

        conteos = (
            pd.Series(
                etiquetas
            )
            .value_counts()
        )

        cluster_minimo = int(
            conteos.min()
        )

        cluster_maximo = int(
            conteos.max()
        )

        resultados.append({
            "k":
                k,

            "inercia":
                float(
                    modelo.inertia_
                ),

            "silhouette":
                float(
                    silhouette
                ),

            "cluster_minimo":
                cluster_minimo,

            "cluster_maximo":
                cluster_maximo,

            "tiempo_kmeans_s":
                float(
                    tiempo_fit
                ),

            "tiempo_silhouette_s":
                float(
                    tiempo_silhouette
                ),

            "silhouette_sample_size":
                SILHOUETTE_SAMPLE_SIZE,
        })

        print(
            f"Inercia          : "
            f"{modelo.inertia_:,.2f}"
        )

        print(
            f"Silhouette       : "
            f"{silhouette:.6f}"
        )

        print(
            f"Cluster mínimo   : "
            f"{cluster_minimo:,}"
        )

        print(
            f"Cluster máximo   : "
            f"{cluster_maximo:,}"
        )

        print(
            f"Tiempo silhouette: "
            f"{tiempo_silhouette:.2f} s"
        )

    return pd.DataFrame(
        resultados
    )


# ============================================================
# GRÁFICA DEL CODO
# ============================================================

def crear_grafica_codo(
    resultados
):

    figura = plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        resultados["k"],
        resultados["inercia"],
        marker="o",
    )

    plt.xlabel(
        "Número de clusters (k)"
    )

    plt.ylabel(
        "Inercia"
    )

    plt.title(
        "Método del codo para selección de k"
    )

    plt.xticks(
        resultados["k"]
    )

    plt.grid(
        True,
        alpha=0.25
    )

    plt.tight_layout()

    ruta = (
        FASE2_DIR
        / "fase2_3_metodo_codo.png"
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
# GRÁFICA SILHOUETTE
# ============================================================

def crear_grafica_silhouette(
    resultados
):

    figura = plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        resultados["k"],
        resultados["silhouette"],
        marker="o",
    )

    mejor = (
        resultados
        .sort_values(
            "silhouette",
            ascending=False
        )
        .iloc[0]
    )

    plt.scatter(
        [
            mejor["k"]
        ],
        [
            mejor["silhouette"]
        ],
        zorder=5,
    )

    plt.annotate(
        (
            f"Mejor silhouette: "
            f"k={int(mejor['k'])}"
        ),
        xy=(
            mejor["k"],
            mejor["silhouette"],
        ),
        xytext=(
            8,
            8,
        ),
        textcoords="offset points",
    )

    plt.xlabel(
        "Número de clusters (k)"
    )

    plt.ylabel(
        "Silhouette score"
    )

    plt.title(
        "Silhouette para selección de k"
    )

    plt.xticks(
        resultados["k"]
    )

    plt.grid(
        True,
        alpha=0.25
    )

    plt.tight_layout()

    ruta = (
        FASE2_DIR
        / "fase2_3_silhouette.png"
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
    print("FASE 2.3 - BLOQUES A/B")
    print("PREPARACIÓN Y SELECCIÓN DE K")
    print("=" * 70)

    print()
    print(
        "[1/4] Cargando únicamente "
        "el corte A..."
    )

    df = cargar_corte_a()

    df = preparar_datos(
        df
    )

    print(
        f"[OK] Filas      : "
        f"{len(df):,}"
    )

    print(
        f"[OK] Positivos  : "
        f"{df['etiqueta'].sum():,}"
    )

    print(
        "[OK] La etiqueta NO se utilizará "
        "para formar los clusters."
    )

    print()
    print(
        "[2/4] Estandarizando features "
        "numéricas y codificando "
        "categóricas..."
    )

    (
        X,
        nombres_transformados,
        tiempo_transformacion,
    ) = transformar_features(
        df
    )

    print(
        f"[OK] Matriz original    : "
        f"{len(df):,} x "
        f"{len(FEATURES)}"
    )

    print(
        f"[OK] Matriz transformada: "
        f"{X.shape[0]:,} x "
        f"{X.shape[1]}"
    )

    print(
        f"[OK] Transformación     : "
        f"{tiempo_transformacion:.2f} s"
    )

    # ----------------------------------------
    # Guardar resumen preparación
    # ----------------------------------------

    resumen_preparacion = (
        pd.DataFrame([
            {
                "filas":
                    len(df),

                "features_originales":
                    len(FEATURES),

                "features_transformadas":
                    X.shape[1],

                "positivos":
                    int(
                        df[
                            "etiqueta"
                        ].sum()
                    ),

                "etiqueta_usada_en_kmeans":
                    False,

                "random_state":
                    RANDOM_STATE,

                "silhouette_sample_size":
                    SILHOUETTE_SAMPLE_SIZE,
            }
        ])
    )

    ruta_preparacion = (
        FASE2_DIR
        / "fase2_3_preparacion.csv"
    )

    resumen_preparacion.to_csv(
        ruta_preparacion,
        index=False
    )

    ruta_features = (
        FASE2_DIR
        / "fase2_3_features_transformadas.txt"
    )

    ruta_features.write_text(
        "\n".join(
            nombres_transformados
        ),
        encoding="utf-8"
    )

    # ----------------------------------------
    # K
    # ----------------------------------------

    print()
    print(
        "[3/4] Probando valores "
        "de k = 2 a 8..."
    )

    resultados = evaluar_k(
        X
    )

    ruta_metricas = (
        FASE2_DIR
        / "fase2_3_metricas_k.csv"
    )

    resultados.to_csv(
        ruta_metricas,
        index=False
    )

    # ----------------------------------------
    # Gráficas
    # ----------------------------------------

    print()
    print(
        "[4/4] Generando gráficas..."
    )

    ruta_codo = (
        crear_grafica_codo(
            resultados
        )
    )

    ruta_silhouette = (
        crear_grafica_silhouette(
            resultados
        )
    )

    # ----------------------------------------
    # RESULTADOS
    # ----------------------------------------

    print()
    print("=" * 70)
    print("RESULTADOS DE K")
    print("=" * 70)

    print(
        resultados[
            [
                "k",
                "inercia",
                "silhouette",
                "cluster_minimo",
                "cluster_maximo",
            ]
        ]
        .to_string(
            index=False
        )
    )

    mejor_silhouette = (
        resultados
        .sort_values(
            "silhouette",
            ascending=False
        )
        .iloc[0]
    )

    print()
    print("=" * 70)
    print("REFERENCIA SILHOUETTE")
    print("=" * 70)

    print(
        f"Mayor silhouette : "
        f"{mejor_silhouette['silhouette']:.6f}"
    )

    print(
        f"k correspondiente : "
        f"{int(mejor_silhouette['k'])}"
    )

    print()
    print(
        "IMPORTANTE: todavía no elegimos "
        "k solamente por este número."
    )

    print(
        "También debemos revisar visualmente "
        "el método del codo."
    )

    print()
    print("=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)

    for ruta in [
        ruta_preparacion,
        ruta_features,
        ruta_metricas,
        ruta_codo,
        ruta_silhouette,
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
    print("BLOQUES 2.3-A/B COMPLETADOS")
    print("=" * 70)

    print(
        "[OK] Se utilizó únicamente corte A."
    )

    print(
        "[OK] Datos numéricos estandarizados."
    )

    print(
        "[OK] Variables categóricas "
        "codificadas con One-Hot."
    )

    print(
        "[OK] Etiqueta excluida del clustering."
    )

    print(
        "[OK] Corte B no fue utilizado."
    )


if __name__ == "__main__":
    main()