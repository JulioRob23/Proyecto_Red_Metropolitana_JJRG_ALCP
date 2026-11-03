from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import sklearn
import matplotlib

from sklearn.model_selection import StratifiedKFold


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

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RANDOM_STATE = 42
N_SPLITS = 5

CORTE = "A"
FECHA_CORTE_ESPERADA = "2026-07-01"

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
]

FEATURES_BINARIAS = [
    "es_multimodal",
]

FEATURES_CATEGORICAS = [
    "modo_mas_usado",
    "zona_mas_frecuente",
]

FEATURES = (
    FEATURES_NUMERICAS
    + FEATURES_BINARIAS
    + FEATURES_CATEGORICAS
)


# ============================================================
# CARGA SEGURA DEL .ENV
# ============================================================

def cargar_env(ruta):
    """
    Lee el archivo .env sin imprimir contraseñas.
    """

    valores = {}

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo .env en: {ruta}"
        )

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

            clave = clave.strip()

            valor = (
                valor
                .strip()
                .strip('"')
                .strip("'")
            )

            valores[clave] = valor

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
# CONEXIÓN
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

    columnas_sql = ",\n        ".join(
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

        nombres_columnas = [
            descripcion[0]
            for descripcion
            in cursor.description
        ]

        datos = pd.DataFrame(
            filas,
            columns=nombres_columnas
        )

    finally:
        conexion.close()

    return datos


# ============================================================
# VALIDACIONES
# ============================================================

def validar_corte_a(df):

    print()
    print("=" * 70)
    print("VALIDACIÓN CORTE A")
    print("=" * 70)

    filas = len(df)

    positivos = int(
        df["etiqueta"].sum()
    )

    negativos = (
        filas
        - positivos
    )

    tasa_positiva = (
        positivos
        / filas
    )

    duplicados = int(
        df["unidad_id"]
        .duplicated()
        .sum()
    )

    fechas = sorted(
        df["fecha_corte"]
        .astype(str)
        .unique()
        .tolist()
    )

    print(
        f"Filas             : {filas:,}"
    )

    print(
        f"Positivos         : {positivos:,}"
    )

    print(
        f"Negativos         : {negativos:,}"
    )

    print(
        f"Tasa positiva     : {tasa_positiva:.4f}"
    )

    print(
        f"Duplicados        : {duplicados:,}"
    )

    print(
        f"Fecha de corte    : {fechas}"
    )

    print("-" * 70)

    if filas != FILAS_ESPERADAS:
        raise RuntimeError(
            "Cantidad de filas inesperada. "
            f"Esperado={FILAS_ESPERADAS}, "
            f"real={filas}"
        )

    if positivos != POSITIVOS_ESPERADOS:
        raise RuntimeError(
            "Cantidad de positivos inesperada. "
            f"Esperado={POSITIVOS_ESPERADOS}, "
            f"real={positivos}"
        )

    if duplicados != 0:
        raise RuntimeError(
            "Se encontraron unidades duplicadas "
            "en el corte A."
        )

    if fechas != [
        FECHA_CORTE_ESPERADA
    ]:
        raise RuntimeError(
            "La fecha de corte no coincide "
            "con el corte A esperado."
        )

    if df["etiqueta"].isna().any():
        raise RuntimeError(
            "La etiqueta del corte A "
            "contiene valores nulos."
        )

    etiquetas = set(
        df["etiqueta"]
        .astype(int)
        .unique()
        .tolist()
    )

    if not etiquetas.issubset(
        {0, 1}
    ):
        raise RuntimeError(
            "La etiqueta contiene valores "
            "distintos de 0 y 1."
        )

    print(
        "[OK] Corte A validado correctamente."
    )

    return {
        "filas": filas,
        "positivos": positivos,
        "negativos": negativos,
        "tasa_positiva": tasa_positiva,
        "duplicados": duplicados,
    }


# ============================================================
# REVISIÓN DE NULOS
# ============================================================

def analizar_features(df):

    resultados = []

    for feature in FEATURES:

        nulos = int(
            df[feature]
            .isna()
            .sum()
        )

        porcentaje_nulos = (
            nulos
            / len(df)
        )

        unicos = int(
            df[feature]
            .nunique(
                dropna=True
            )
        )

        resultados.append({
            "feature": feature,
            "tipo": str(
                df[feature].dtype
            ),
            "nulos": nulos,
            "proporcion_nulos":
                round(
                    porcentaje_nulos,
                    6
                ),
            "valores_unicos": unicos,
        })

    resumen = pd.DataFrame(
        resultados
    )

    ruta = (
        OUTPUT_DIR
        / "fase1_4_nulos_features.csv"
    )

    resumen.to_csv(
        ruta,
        index=False
    )

    print()
    print("=" * 70)
    print("REVISIÓN DE FEATURES")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print(
        f"[OK] Resumen guardado en: "
        f"{ruta.relative_to(PROJECT_ROOT)}"
    )

    return resumen


# ============================================================
# CONSTRUIR FOLDS ESTRATIFICADOS
# ============================================================

def construir_folds(df):

    y = (
        df["etiqueta"]
        .astype(int)
        .to_numpy()
    )

    skf = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    folds = np.zeros(
        len(df),
        dtype=int
    )

    X_dummy = np.zeros(
        (
            len(df),
            1
        )
    )

    for numero_fold, (
        _,
        indices_validacion,
    ) in enumerate(
        skf.split(
            X_dummy,
            y
        ),
        start=1,
    ):

        folds[
            indices_validacion
        ] = numero_fold

    if np.any(
        folds == 0
    ):
        raise RuntimeError(
            "Hay filas sin fold asignado."
        )

    asignaciones = pd.DataFrame({
        "unidad_id":
            df["unidad_id"],
        "etiqueta": y,
        "fold": folds,
    })

    ruta_folds = (
        OUTPUT_DIR
        / "fase1_4_folds.csv"
    )

    asignaciones.to_csv(
        ruta_folds,
        index=False
    )

    resumen = (
        asignaciones
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

    ruta_resumen = (
        OUTPUT_DIR
        / "fase1_4_folds_resumen.csv"
    )

    resumen.to_csv(
        ruta_resumen,
        index=False
    )

    print()
    print("=" * 70)
    print("FOLDS ESTRATIFICADOS")
    print("=" * 70)

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print(
        f"[OK] Folds guardados en: "
        f"{ruta_folds.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"[OK] Resumen guardado en: "
        f"{ruta_resumen.relative_to(PROJECT_ROOT)}"
    )

    return asignaciones, resumen


# ============================================================
# GUARDAR RESUMEN DEL BLOQUE A
# ============================================================

def guardar_resumen(
    validacion
):

    resumen = pd.DataFrame([
        {
            "metrica":
                "filas_corte_A",
            "valor":
                validacion["filas"],
        },
        {
            "metrica":
                "positivos",
            "valor":
                validacion["positivos"],
        },
        {
            "metrica":
                "negativos",
            "valor":
                validacion["negativos"],
        },
        {
            "metrica":
                "tasa_positiva",
            "valor":
                round(
                    validacion[
                        "tasa_positiva"
                    ],
                    6
                ),
        },
        {
            "metrica":
                "duplicados",
            "valor":
                validacion[
                    "duplicados"
                ],
        },
        {
            "metrica":
                "n_folds",
            "valor":
                N_SPLITS,
        },
        {
            "metrica":
                "random_state",
            "valor":
                RANDOM_STATE,
        },
    ])

    ruta = (
        OUTPUT_DIR
        / "fase1_4_bloque_a_resumen.csv"
    )

    resumen.to_csv(
        ruta,
        index=False
    )

    return ruta


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FASE 1.4 - BLOQUE A")
    print("PREPARACIÓN DEL CORTE A")
    print("=" * 70)

    print()
    print("Versiones:")
    print(
        f"pandas        : {pd.__version__}"
    )
    print(
        f"numpy         : {np.__version__}"
    )
    print(
        f"scikit-learn  : {sklearn.__version__}"
    )
    print(
        f"matplotlib    : {matplotlib.__version__}"
    )

    df = cargar_corte_a()

    validacion = validar_corte_a(
        df
    )

    analizar_features(
        df
    )

    construir_folds(
        df
    )

    ruta_resumen = guardar_resumen(
        validacion
    )

    print()
    print("=" * 70)
    print("BLOQUE A COMPLETADO")
    print("=" * 70)

    print(
        f"Filas     : "
        f"{validacion['filas']:,}"
    )

    print(
        f"Positivos : "
        f"{validacion['positivos']:,}"
    )

    print(
        f"Tasa      : "
        f"{validacion['tasa_positiva']:.4f}"
    )

    print(
        f"Folds     : {N_SPLITS}"
    )

    print(
        f"Semilla   : {RANDOM_STATE}"
    )

    print(
        f"Resumen   : "
        f"{ruta_resumen.relative_to(PROJECT_ROOT)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()