from pathlib import Path

import pandas as pd
import psycopg2


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

FASE2_DIR.mkdir(
    parents=True,
    exist_ok=True
)

FOLDS_PATH = (
    FASE1_DIR
    / "fase1_4_folds.csv"
)

RESULTADOS_FASE1_PATH = (
    FASE1_DIR
    / "fase1_4_resultados_modelos.csv"
)


# ============================================================
# CONSTANTES ESPERADAS
# ============================================================

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310
NEGATIVOS_ESPERADOS = 51689
N_FOLDS_ESPERADOS = 5

MEJOR_LOGISTICA_AP_ESPERADA = 0.460007


# ============================================================
# FEATURES OFICIALES
# EXACTAMENTE LAS MISMAS DE 1.4
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
            f"No se encontró .env en {ENV_PATH}"
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

    requeridas = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    ]

    faltantes = [
        clave
        for clave in requeridas
        if clave not in valores
    ]

    if faltantes:
        raise RuntimeError(
            "Faltan variables en .env: "
            + ", ".join(faltantes)
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
# CARGAR ÚNICAMENTE CORTE A
# ============================================================

def cargar_corte_a():

    columnas = [
        "unidad_id",
        "fecha_corte",
        "corte",
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
# VALIDAR FOLDS
# ============================================================

def validar_folds(df):

    if not FOLDS_PATH.exists():

        raise FileNotFoundError(
            "No se encontró el archivo "
            "fase1_4_folds.csv"
        )

    folds = pd.read_csv(
        FOLDS_PATH
    )

    combinado = df.merge(
        folds,
        on="unidad_id",
        how="inner",
        suffixes=(
            "_db",
            "_fold"
        ),
        validate="one_to_one",
    )

    if len(combinado) != FILAS_ESPERADAS:

        raise RuntimeError(
            "La cantidad de filas después "
            "del merge no coincide."
        )

    if not (
        combinado[
            "etiqueta_db"
        ].astype(int)
        ==
        combinado[
            "etiqueta_fold"
        ].astype(int)
    ).all():

        raise RuntimeError(
            "Las etiquetas no coinciden "
            "con los folds oficiales."
        )

    combinado["etiqueta"] = (
        combinado[
            "etiqueta_db"
        ].astype(int)
    )

    if (
        combinado["fold"].nunique()
        != N_FOLDS_ESPERADOS
    ):

        raise RuntimeError(
            "No hay exactamente 5 folds."
        )

    return combinado


# ============================================================
# VALIDAR POBLACIÓN
# ============================================================

def validar_poblacion(df):

    filas = len(df)

    positivos = int(
        df["etiqueta"].sum()
    )

    negativos = (
        filas
        - positivos
    )

    tasa = (
        positivos
        / filas
    )

    duplicados = int(
        df["unidad_id"]
        .duplicated()
        .sum()
    )

    if filas != FILAS_ESPERADAS:
        raise RuntimeError(
            f"Filas incorrectas: {filas}"
        )

    if positivos != POSITIVOS_ESPERADOS:
        raise RuntimeError(
            f"Positivos incorrectos: {positivos}"
        )

    if negativos != NEGATIVOS_ESPERADOS:
        raise RuntimeError(
            f"Negativos incorrectos: {negativos}"
        )

    if duplicados != 0:
        raise RuntimeError(
            "Se encontraron usuarios duplicados."
        )

    return {
        "filas": filas,
        "positivos": positivos,
        "negativos": negativos,
        "tasa_positiva": tasa,
        "duplicados": duplicados,
    }


# ============================================================
# RESUMEN DE FOLDS
# ============================================================

def resumir_folds(df):

    resumen = (
        df
        .groupby(
            "fold",
            as_index=False
        )
        .agg(
            filas=(
                "unidad_id",
                "count"
            ),
            positivos=(
                "etiqueta",
                "sum"
            ),
        )
    )

    resumen["negativos"] = (
        resumen["filas"]
        - resumen["positivos"]
    )

    resumen["tasa_positiva"] = (
        resumen["positivos"]
        / resumen["filas"]
    ).round(4)

    return resumen


# ============================================================
# REVISAR FEATURES
# ============================================================

def revisar_features(df):

    filas = []

    for feature in FEATURES:

        filas.append({
            "feature":
                feature,
            "tipo":
                str(
                    df[feature].dtype
                ),
            "nulos":
                int(
                    df[feature]
                    .isna()
                    .sum()
                ),
            "valores_unicos":
                int(
                    df[feature]
                    .nunique(
                        dropna=True
                    )
                ),
        })

    return pd.DataFrame(
        filas
    )


# ============================================================
# RECUPERAR REFERENCIA DE FASE 1
# ============================================================

def cargar_referencia_logistica():

    if not RESULTADOS_FASE1_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase1_4_resultados_modelos.csv"
        )

    resultados = pd.read_csv(
        RESULTADOS_FASE1_PATH
    )

    logistica_l2 = (
        resultados[
            resultados[
                "modelo"
            ]
            == "Logística L2"
        ]
    )

    if logistica_l2.empty:

        raise RuntimeError(
            "No se encontró Logística L2 "
            "en resultados de Fase 1."
        )

    fila = (
        logistica_l2
        .iloc[0]
    )

    return {
        "modelo":
            fila["modelo"],
        "configuracion":
            fila["configuracion"],
        "ap_media":
            float(
                fila["ap_media"]
            ),
        "ap_std":
            float(
                fila["ap_std"]
            ),
    }


# ============================================================
# GUARDAR ARTEFACTOS
# ============================================================

def guardar_resultados(
    poblacion,
    resumen_folds,
    resumen_features,
    referencia,
):

    resumen_general = pd.DataFrame([
        {
            "metrica":
                "filas_corte_A",
            "valor":
                poblacion["filas"],
        },
        {
            "metrica":
                "positivos",
            "valor":
                poblacion["positivos"],
        },
        {
            "metrica":
                "negativos",
            "valor":
                poblacion["negativos"],
        },
        {
            "metrica":
                "tasa_positiva",
            "valor":
                round(
                    poblacion[
                        "tasa_positiva"
                    ],
                    6
                ),
        },
        {
            "metrica":
                "numero_folds",
            "valor":
                N_FOLDS_ESPERADOS,
        },
        {
            "metrica":
                "logistica_l2_ap_media",
            "valor":
                referencia[
                    "ap_media"
                ],
        },
        {
            "metrica":
                "logistica_l2_ap_std",
            "valor":
                referencia[
                    "ap_std"
                ],
        },
    ])

    ruta_general = (
        FASE2_DIR
        / "fase2_1_preparacion_resumen.csv"
    )

    ruta_folds = (
        FASE2_DIR
        / "fase2_1_folds_verificados.csv"
    )

    ruta_features = (
        FASE2_DIR
        / "fase2_1_features_verificadas.csv"
    )

    resumen_general.to_csv(
        ruta_general,
        index=False
    )

    resumen_folds.to_csv(
        ruta_folds,
        index=False
    )

    resumen_features.to_csv(
        ruta_features,
        index=False
    )

    return (
        ruta_general,
        ruta_folds,
        ruta_features,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 2.1 - BLOQUE A")
    print("PREPARACIÓN PARA ENSEMBLE")
    print("=" * 70)

    datos = cargar_corte_a()

    combinado = validar_folds(
        datos
    )

    poblacion = validar_poblacion(
        combinado
    )

    resumen_folds = resumir_folds(
        combinado
    )

    resumen_features = revisar_features(
        combinado
    )

    referencia = cargar_referencia_logistica()

    print()
    print("=" * 70)
    print("POBLACIÓN CORTE A")
    print("=" * 70)

    print(
        f"Filas         : "
        f"{poblacion['filas']:,}"
    )

    print(
        f"Positivos     : "
        f"{poblacion['positivos']:,}"
    )

    print(
        f"Negativos     : "
        f"{poblacion['negativos']:,}"
    )

    print(
        f"Tasa positiva : "
        f"{poblacion['tasa_positiva']:.4f}"
    )

    print(
        f"Duplicados    : "
        f"{poblacion['duplicados']}"
    )

    print()
    print("=" * 70)
    print("FOLDS OFICIALES")
    print("=" * 70)

    print(
        resumen_folds.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("REFERENCIA FASE 1")
    print("=" * 70)

    print(
        f"Modelo        : "
        f"{referencia['modelo']}"
    )

    print(
        f"Configuración : "
        f"{referencia['configuracion']}"
    )

    print(
        f"AP media      : "
        f"{referencia['ap_media']:.6f}"
    )

    print(
        f"AP std        : "
        f"{referencia['ap_std']:.6f}"
    )

    print()
    print("=" * 70)
    print("NULOS EN FEATURES")
    print("=" * 70)

    print(
        resumen_features.to_string(
            index=False
        )
    )

    (
        ruta_general,
        ruta_folds,
        ruta_features,
    ) = guardar_resultados(
        poblacion,
        resumen_folds,
        resumen_features,
        referencia,
    )

    print()
    print("=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)

    for ruta in [
        ruta_general,
        ruta_folds,
        ruta_features,
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
    print("BLOQUE A COMPLETADO")
    print("=" * 70)

    print(
        "[OK] Solo se utilizó corte A."
    )

    print(
        "[OK] No se consultó la etiqueta "
        "del corte B."
    )

    print(
        "[OK] Se reutilizarán exactamente "
        "los 5 folds de Fase 1."
    )


if __name__ == "__main__":
    main()