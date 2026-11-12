from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2


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

SEGMENTOS_PATH = (
    FASE2_DIR
    / "fase2_3_segmentos_pca.csv"
)


# ============================================================
# CONTROLES
# ============================================================

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
        port=int(
            env["POSTGRES_PORT"]
        ),
    )


# ============================================================
# CARGAR FEATURES CORTE A
# ============================================================

def cargar_features_a():

    columnas = [
        "unidad_id",
        *FEATURES_NUMERICAS,
        *FEATURES_CATEGORICAS,
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
# PREPARAR
# ============================================================

def preparar_datos():

    if not SEGMENTOS_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_3_segmentos_pca.csv"
        )

    features = cargar_features_a()

    segmentos = pd.read_csv(
        SEGMENTOS_PATH
    )

    if len(features) != FILAS_ESPERADAS:

        raise RuntimeError(
            "Cantidad incorrecta "
            "de filas de features."
        )

    if len(segmentos) != FILAS_ESPERADAS:

        raise RuntimeError(
            "Cantidad incorrecta "
            "de asignaciones."
        )

    # ----------------------------------------
    # Convertir numéricas
    # ----------------------------------------

    for columna in FEATURES_NUMERICAS:

        if columna == "es_multimodal":

            features[columna] = (
                features[columna]
                .astype(int)
                .astype(float)
            )

        else:

            features[columna] = (
                pd.to_numeric(
                    features[columna],
                    errors="coerce"
                )
                .astype(float)
            )

    features["etiqueta"] = (
        features["etiqueta"]
        .astype(int)
    )

    # ----------------------------------------
    # Merge
    # ----------------------------------------

    df = features.merge(
        segmentos[
            [
                "unidad_id",
                "segmento",
            ]
        ],
        on="unidad_id",
        how="inner",
        validate="one_to_one",
    )

    if len(df) != FILAS_ESPERADAS:

        raise RuntimeError(
            "El merge no produjo "
            "59,999 filas."
        )

    if int(
        df["etiqueta"].sum()
    ) != POSITIVOS_ESPERADOS:

        raise RuntimeError(
            "Positivos incorrectos."
        )

    return df


# ============================================================
# MODA SEGURA
# ============================================================

def moda_serie(
    serie
):

    moda = (
        serie
        .dropna()
        .mode()
    )

    if len(moda) == 0:
        return "SIN_DATO"

    return str(
        moda.iloc[0]
    )


# ============================================================
# PERFIL GENERAL
# ============================================================

def crear_perfiles(
    df
):

    perfiles = []

    for segmento in sorted(
        df["segmento"].unique()
    ):

        datos = (
            df[
                df["segmento"]
                == segmento
            ]
        )

        fila = {
            "segmento":
                int(segmento),

            "tamanio":
                int(
                    len(datos)
                ),

            "proporcion_poblacion":
                float(
                    len(datos)
                    / len(df)
                ),

            "positivos":
                int(
                    datos[
                        "etiqueta"
                    ].sum()
                ),

            "tasa_abandono":
                float(
                    datos[
                        "etiqueta"
                    ].mean()
                ),

            "modo_mas_usado_moda":
                moda_serie(
                    datos[
                        "modo_mas_usado"
                    ]
                ),

            "zona_mas_frecuente_moda":
                moda_serie(
                    datos[
                        "zona_mas_frecuente"
                    ]
                ),
        }

        for feature in (
            FEATURES_NUMERICAS
        ):

            fila[
                f"mediana_{feature}"
            ] = float(
                datos[
                    feature
                ].median()
            )

        perfiles.append(
            fila
        )

    return pd.DataFrame(
        perfiles
    )


# ============================================================
# REFERENCIA GLOBAL
# ============================================================

def crear_referencia_global(
    df
):

    fila = {
        "grupo":
            "Población completa A",

        "tamanio":
            len(df),

        "tasa_abandono":
            float(
                df[
                    "etiqueta"
                ].mean()
            ),
    }

    for feature in (
        FEATURES_NUMERICAS
    ):

        fila[
            f"mediana_{feature}"
        ] = float(
            df[
                feature
            ].median()
        )

    fila[
        "modo_mas_usado_moda"
    ] = moda_serie(
        df[
            "modo_mas_usado"
        ]
    )

    fila[
        "zona_mas_frecuente_moda"
    ] = moda_serie(
        df[
            "zona_mas_frecuente"
        ]
    )

    return pd.DataFrame([
        fila
    ])


# ============================================================
# TABLA COMPACTA
# ============================================================

def crear_tabla_compacta(
    perfiles
):

    columnas = [
        "segmento",
        "tamanio",
        "proporcion_poblacion",
        "tasa_abandono",

        "mediana_viajes_7d",
        "mediana_viajes_14d",
        "mediana_viajes_28d",

        "mediana_dias_activos_28d",
        "mediana_dias_desde_ultimo_viaje",

        "mediana_cantidad_modos_28d",
        "mediana_es_multimodal",

        "mediana_gasto_total_28d",
        "mediana_gasto_promedio_28d",

        "mediana_proporcion_hora_pico",
        "mediana_proporcion_dia_habil",

        "modo_mas_usado_moda",
        "zona_mas_frecuente_moda",
    ]

    return perfiles[
        columnas
    ].copy()


# ============================================================
# DIFERENCIA CONTRA MEDIANA GLOBAL
# ============================================================

def crear_comparacion_global(
    perfiles,
    referencia
):

    resultado = []

    global_row = (
        referencia.iloc[0]
    )

    features_clave = [
        "viajes_7d",
        "viajes_14d",
        "viajes_28d",
        "dias_activos_28d",
        "dias_desde_ultimo_viaje",
        "cantidad_modos_28d",
        "gasto_total_28d",
        "gasto_promedio_28d",
    ]

    for _, fila in (
        perfiles.iterrows()
    ):

        salida = {
            "segmento":
                int(
                    fila["segmento"]
                )
        }

        for feature in (
            features_clave
        ):

            columna = (
                f"mediana_{feature}"
            )

            valor_segmento = float(
                fila[columna]
            )

            valor_global = float(
                global_row[columna]
            )

            salida[
                f"{feature}_segmento"
            ] = valor_segmento

            salida[
                f"{feature}_global"
            ] = valor_global

            if valor_global != 0:

                salida[
                    f"{feature}_ratio_global"
                ] = (
                    valor_segmento
                    / valor_global
                )

            else:

                salida[
                    f"{feature}_ratio_global"
                ] = np.nan

        resultado.append(
            salida
        )

    return pd.DataFrame(
        resultado
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 78)
    print("FASE 2.3 - BLOQUE D")
    print("PERFILES DE LOS SEGMENTOS")
    print("=" * 78)

    df = preparar_datos()

    perfiles = crear_perfiles(
        df
    )

    referencia = (
        crear_referencia_global(
            df
        )
    )

    compacta = (
        crear_tabla_compacta(
            perfiles
        )
    )

    comparacion = (
        crear_comparacion_global(
            perfiles,
            referencia,
        )
    )

    # ----------------------------------------
    # Guardar
    # ----------------------------------------

    ruta_perfiles = (
        FASE2_DIR
        / "fase2_3_perfiles_completos.csv"
    )

    ruta_compacta = (
        FASE2_DIR
        / "fase2_3_perfiles_compactos.csv"
    )

    ruta_global = (
        FASE2_DIR
        / "fase2_3_referencia_global.csv"
    )

    ruta_comparacion = (
        FASE2_DIR
        / "fase2_3_comparacion_mediana_global.csv"
    )

    perfiles.to_csv(
        ruta_perfiles,
        index=False
    )

    compacta.to_csv(
        ruta_compacta,
        index=False
    )

    referencia.to_csv(
        ruta_global,
        index=False
    )

    comparacion.to_csv(
        ruta_comparacion,
        index=False
    )

    # ----------------------------------------
    # Mostrar referencia
    # ----------------------------------------

    print()
    print("=" * 78)
    print("REFERENCIA GLOBAL CORTE A")
    print("=" * 78)

    print(
        f"Tamaño              : "
        f"{len(df):,}"
    )

    print(
        f"Tasa abandono       : "
        f"{df['etiqueta'].mean():.4f}"
    )

    print(
        f"Mediana viajes 7d   : "
        f"{df['viajes_7d'].median():.2f}"
    )

    print(
        f"Mediana viajes 14d  : "
        f"{df['viajes_14d'].median():.2f}"
    )

    print(
        f"Mediana viajes 28d  : "
        f"{df['viajes_28d'].median():.2f}"
    )

    print(
        "Mediana días último : "
        f"{df['dias_desde_ultimo_viaje'].median():.2f}"
    )

    print(
        f"Mediana gasto total : "
        f"Q{df['gasto_total_28d'].median():.2f}"
    )

    # ----------------------------------------
    # Mostrar perfiles
    # ----------------------------------------

    print()
    print("=" * 78)
    print("PERFILES COMPACTOS")
    print("=" * 78)

    columnas_mostrar = [
        "segmento",
        "tamanio",
        "tasa_abandono",
        "mediana_viajes_7d",
        "mediana_viajes_14d",
        "mediana_viajes_28d",
        "mediana_dias_activos_28d",
        "mediana_dias_desde_ultimo_viaje",
        "mediana_cantidad_modos_28d",
        "mediana_gasto_total_28d",
        "modo_mas_usado_moda",
        "zona_mas_frecuente_moda",
    ]

    print(
        compacta[
            columnas_mostrar
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("PROPORCIONES DE USO POR SEGMENTO")
    print("=" * 78)

    columnas_proporciones = [
        "segmento",
        "mediana_proporcion_transmetro",
        "mediana_proporcion_transurbano",
        "mediana_proporcion_metroriel",
        "mediana_proporcion_aerometro",
        "mediana_proporcion_hora_pico",
        "mediana_proporcion_dia_habil",
    ]

    print(
        perfiles[
            columnas_proporciones
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("ARCHIVOS GENERADOS")
    print("=" * 78)

    for ruta in [
        ruta_perfiles,
        ruta_compacta,
        ruta_global,
        ruta_comparacion,
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
    print("=" * 78)
    print("BLOQUE D COMPLETADO")
    print("=" * 78)

    print(
        "[OK] Perfiles calculados "
        "con medianas."
    )

    print(
        "[OK] Tasa de abandono usada "
        "solo de forma descriptiva."
    )

    print(
        "[OK] Ya podemos interpretar "
        "y nombrar los segmentos."
    )


if __name__ == "__main__":
    main()