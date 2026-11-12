from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

import joblib
import pandas as pd
import psycopg2


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

ENV_PATH = PROJECT_ROOT / ".env"

DATOS_RED_DIR = (
    PROJECT_ROOT
    / "datos_red"
)

FLOW_PATH = (
    PROJECT_ROOT
    / "orchestration"
    / "flujo_proyecto2.py"
)

DBT_DIR = (
    PROJECT_ROOT
    / "dbt"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "modelo_churn_p2_hgb_v1.joblib"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "models"
    / "modelo_churn_p2_hgb_v1.metadata.json"
)

PREDICCIONES_DIR = (
    PROJECT_ROOT
    / "predicciones"
)

PREDICCIONES_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FECHA DE PRODUCCIÓN OFICIAL
# ============================================================

CORTE_C = "2026-08-30"


# ============================================================
# UTILIDADES
# ============================================================

def calcular_sha256(ruta):

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
# .ENV
# ============================================================

def cargar_env():

    if not ENV_PATH.exists():

        raise FileNotFoundError(
            "No se encontró .env"
        )

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
# MODELO Y METADATA
# ============================================================

def cargar_metadata():

    if not METADATA_PATH.exists():

        raise FileNotFoundError(
            "No se encontró el metadata "
            "del modelo."
        )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        metadata = json.load(
            archivo
        )

    return metadata


def cargar_modelo():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            "No se encontró el modelo "
            "final guardado."
        )

    metadata = cargar_metadata()

    sha_actual = calcular_sha256(
        MODEL_PATH
    )

    sha_esperado = metadata[
        "sha256"
    ]

    if sha_actual != sha_esperado:

        raise RuntimeError(
            "El SHA256 del modelo no coincide "
            "con el metadata."
        )

    modelo = joblib.load(
        MODEL_PATH
    )

    return (
        modelo,
        metadata,
    )


# ============================================================
# VALIDAR CARPETA DE DATOS
# ============================================================

def validar_carpeta_datos(
    ruta
):

    ruta = (
        Path(ruta)
        .expanduser()
        .resolve()
    )

    if not ruta.exists():

        raise FileNotFoundError(
            f"No existe la carpeta: {ruta}"
        )

    if not ruta.is_dir():

        raise NotADirectoryError(
            f"No es una carpeta: {ruta}"
        )

    archivos = [
        archivo
        for archivo in ruta.rglob("*")
        if archivo.is_file()
    ]

    if len(archivos) == 0:

        raise RuntimeError(
            "La carpeta de datos está vacía."
        )

    return (
        ruta,
        archivos,
    )


# ============================================================
# SINCRONIZAR DATOS PARA EL FLUJO
# ============================================================

def sincronizar_datos(
    origen
):

    origen = origen.resolve()
    destino = DATOS_RED_DIR.resolve()

    if origen == destino:

        print(
            "[OK] --datos ya apunta a datos_red."
        )

        return

    print(
        "[...] Copiando carpeta recibida "
        "a datos_red..."
    )

    if DATOS_RED_DIR.exists():

        shutil.rmtree(
            DATOS_RED_DIR
        )

    shutil.copytree(
        origen,
        DATOS_RED_DIR
    )

    print(
        "[OK] Datos sincronizados."
    )


# ============================================================
# EJECUTAR COMANDO
# ============================================================

def ejecutar_comando(
    comando,
    descripcion
):

    print()
    print(
        f"[...] {descripcion}"
    )

    print(
        "      "
        + " ".join(
            str(x)
            for x in comando
        )
    )

    subprocess.run(
        comando,
        cwd=PROJECT_ROOT,
        check=True,
    )

    print(
        f"[OK] {descripcion}"
    )


# ============================================================
# FLUJO COMPLETO
# ============================================================

def ejecutar_flujo_desde_cero(
    datos
):

    sincronizar_datos(
        datos
    )

    if not FLOW_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "orchestration/flujo_proyecto2.py"
        )

    ejecutar_comando(
        [
            sys.executable,
            str(FLOW_PATH),
            "--desde-cero",
        ],
        (
            "Ejecutando pipeline completo "
            "desde cero"
        ),
    )


# ============================================================
# MATERIALIZAR FEATURES DEL CORTE
# ============================================================

def materializar_features(
    fecha_corte
):

    vars_dbt = (
        "{fecha_corte: '"
        + fecha_corte
        + "'}"
    )

    comando = [
        "dbt",
        "run",
        "--project-dir",
        str(DBT_DIR),
        "--profiles-dir",
        str(DBT_DIR),
        "--select",
        "features_usuario",
        "--vars",
        vars_dbt,
    ]

    ejecutar_comando(
        comando,
        (
            "Materializando features para "
            f"fecha de corte {fecha_corte}"
        ),
    )


# ============================================================
# CARGAR FEATURES
# ============================================================

def cargar_features(
    fecha_corte,
    features
):

    columnas_sql = ",\n            ".join(
        [
            "unidad_id",
            *features,
        ]
    )

    consulta = f"""
        SELECT
            {columnas_sql}
        FROM features.features_usuario
        WHERE fecha_corte::date = %s::date
        ORDER BY unidad_id;
    """

    conexion = conectar_postgres()

    try:

        cursor = conexion.cursor()

        cursor.execute(
            consulta,
            (
                fecha_corte,
            )
        )

        filas = cursor.fetchall()

        columnas = [
            descripcion[0]
            for descripcion
            in cursor.description
        ]

        df = pd.DataFrame(
            filas,
            columns=columnas
        )

    finally:

        conexion.close()

    if len(df) == 0:

        raise RuntimeError(
            "No se encontraron features "
            f"para el corte {fecha_corte}."
        )

    if (
        df["unidad_id"]
        .duplicated()
        .any()
    ):

        raise RuntimeError(
            "Hay unidades duplicadas "
            "en las features."
        )

    return df


# ============================================================
# PREPARAR TIPOS
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

    nulos = int(
        df[features]
        .isna()
        .sum()
        .sum()
    )

    if nulos != 0:

        raise RuntimeError(
            "Se encontraron "
            f"{nulos} valores nulos "
            "en las features."
        )

    return df


# ============================================================
# LLAVES ORIGINALES DE LA UNIDAD
# ============================================================

def cargar_tarjetas():

    consulta = """
        SELECT
            usuario_id AS unidad_id,

            string_agg(
                DISTINCT clave_fuente,
                ';'
                ORDER BY clave_fuente
            ) AS tarjetas

        FROM silver.bridge_identidad_usuarios

        GROUP BY usuario_id

        ORDER BY usuario_id;
    """

    conexion = conectar_postgres()

    try:

        df = pd.read_sql_query(
            consulta,
            conexion
        )

    finally:

        conexion.close()

    return df


# ============================================================
# RUTA DE SALIDA
# ============================================================

def obtener_ruta_salida(
    fecha_corte,
    salida_arg
):

    if salida_arg:

        ruta = (
            Path(salida_arg)
            .expanduser()
        )

        if not ruta.is_absolute():

            ruta = (
                PROJECT_ROOT
                / ruta
            )

        ruta = ruta.resolve()

    elif fecha_corte == CORTE_C:

        ruta = (
            PREDICCIONES_DIR
            / "predicciones_corte_C.csv"
        )

    else:

        fecha_nombre = (
            fecha_corte
            .replace(
                "-",
                "_"
            )
        )

        ruta = (
            PREDICCIONES_DIR
            / (
                "predicciones_"
                + fecha_nombre
                + ".csv"
            )
        )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return ruta


# ============================================================
# GENERAR PREDICCIONES
# ============================================================

def generar_predicciones(
    fecha_corte,
    salida
):

    modelo, metadata = (
        cargar_modelo()
    )

    features = metadata[
        "features"
    ]

    umbral = float(
        metadata[
            "umbral"
        ]
    )

    print()
    print(
        "[...] Cargando features "
        f"del corte {fecha_corte}..."
    )

    df = cargar_features(
        fecha_corte,
        features,
    )

    df = preparar_features(
        df,
        features,
    )

    print(
        f"[OK] Población del corte: "
        f"{len(df):,}"
    )

    print()
    print(
        "[...] Cargando llaves "
        "originales de las unidades..."
    )

    tarjetas = cargar_tarjetas()

    resultado = df[
        [
            "unidad_id",
        ]
    ].merge(
        tarjetas,
        on="unidad_id",
        how="left",
        validate="one_to_one",
    )

    faltantes = int(
        resultado[
            "tarjetas"
        ]
        .isna()
        .sum()
    )

    if faltantes != 0:

        raise RuntimeError(
            f"{faltantes} unidades no tienen "
            "llaves originales en el bridge."
        )

    print(
        "[OK] Llaves originales "
        "asociadas."
    )

    print()
    print(
        "[...] Cargando modelo guardado "
        "y calculando puntajes..."
    )

    puntajes = (
        modelo
        .predict_proba(
            df[features]
        )[:, 1]
    )

    resultado[
        "puntaje"
    ] = puntajes

    resultado[
        "contactar"
    ] = (
        resultado[
            "puntaje"
        ]
        >= umbral
    ).astype(int)

    resultado = (
        resultado[
            [
                "unidad_id",
                "tarjetas",
                "puntaje",
                "contactar",
            ]
        ]
        .sort_values(
            "unidad_id"
        )
        .reset_index(
            drop=True
        )
    )

    resultado.to_csv(
        salida,
        index=False,
        float_format="%.12f",
        encoding="utf-8",
    )

    sha_csv = calcular_sha256(
        salida
    )

    contactados = int(
        resultado[
            "contactar"
        ].sum()
    )

    print(
        "[OK] Predicciones generadas."
    )

    return {
        "resultado":
            resultado,

        "umbral":
            umbral,

        "contactados":
            contactados,

        "sha256":
            sha_csv,

        "metadata":
            metadata,
    }


# ============================================================
# MANIFEST
# ============================================================

def guardar_manifest(
    fecha_corte,
    datos,
    salida,
    info,
    usar_db_existente,
):

    manifest_path = (
        salida.parent
        / (
            salida.stem
            + ".manifest.json"
        )
    )

    contenido = {
        "fecha_generacion":
            datetime.now()
            .astimezone()
            .isoformat(),

        "fecha_corte":
            fecha_corte,

        "carpeta_datos":
            str(datos),

        "modo":
            (
                "db_existente"
                if usar_db_existente
                else "pipeline_desde_cero"
            ),

        "modelo":
            info[
                "metadata"
            ][
                "archivo_modelo"
            ],

        "modelo_sha256":
            info[
                "metadata"
            ][
                "sha256"
            ],

        "umbral":
            info[
                "umbral"
            ],

        "filas":
            len(
                info[
                    "resultado"
                ]
            ),

        "contactados":
            info[
                "contactados"
            ],

        "csv":
            str(
                salida.relative_to(
                    PROJECT_ROOT
                )
            ),

        "csv_sha256":
            info[
                "sha256"
            ],
    }

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            contenido,
            archivo,
            indent=2,
            ensure_ascii=False,
        )

    return manifest_path


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Genera predicciones de abandono "
            "para una fecha de corte."
        )
    )

    parser.add_argument(
        "--datos",
        required=True,
        help=(
            "Carpeta que contiene los "
            "archivos fuente."
        ),
    )

    parser.add_argument(
        "--fecha-corte",
        required=True,
        help=(
            "Fecha de corte en formato "
            "YYYY-MM-DD."
        ),
    )

    parser.add_argument(
        "--salida",
        default=None,
        help=(
            "Ruta opcional del CSV "
            "de predicciones."
        ),
    )

    parser.add_argument(
        "--usar-db-existente",
        action="store_true",
        help=(
            "Modo local: omite la ingesta "
            "desde cero y utiliza las tablas "
            "Silver existentes."
        ),
    )

    args = parser.parse_args()

    fecha_corte = args.fecha_corte

    try:

        datetime.strptime(
            fecha_corte,
            "%Y-%m-%d"
        )

    except ValueError as exc:

        raise ValueError(
            "--fecha-corte debe usar "
            "formato YYYY-MM-DD."
        ) from exc

    datos, archivos = (
        validar_carpeta_datos(
            args.datos
        )
    )

    salida = obtener_ruta_salida(
        fecha_corte,
        args.salida,
    )

    print()
    print("=" * 76)
    print("PREDICCIÓN DE ABANDONO - RED METROPOLITANA")
    print("=" * 76)

    print()
    print(
        f"Carpeta de datos : {datos}"
    )

    print(
        f"Archivos         : "
        f"{len(archivos)}"
    )

    print(
        f"Fecha de corte   : "
        f"{fecha_corte}"
    )

    print(
        f"Salida           : "
        f"{salida}"
    )

    print(
        f"DB existente     : "
        f"{args.usar_db_existente}"
    )

    # ----------------------------------------
    # MODO OFICIAL
    # ----------------------------------------

    if not args.usar_db_existente:

        print()
        print("=" * 76)
        print("1. PIPELINE DE DATOS")
        print("=" * 76)

        ejecutar_flujo_desde_cero(
            datos
        )

    else:

        print()
        print(
            "[MODO LOCAL] Se omite la "
            "ingesta completa."
        )

        print(
            "[MODO LOCAL] Se utilizarán "
            "las tablas Silver existentes."
        )

    # ----------------------------------------
    # FEATURES DEL CORTE
    # ----------------------------------------

    print()
    print("=" * 76)
    print("2. FEATURES DEL CORTE")
    print("=" * 76)

    materializar_features(
        fecha_corte
    )

    # ----------------------------------------
    # PREDICCIÓN
    # ----------------------------------------

    print()
    print("=" * 76)
    print("3. MODELO GUARDADO Y PREDICCIÓN")
    print("=" * 76)

    info = generar_predicciones(
        fecha_corte,
        salida,
    )

    manifest = guardar_manifest(
        fecha_corte,
        datos,
        salida,
        info,
        args.usar_db_existente,
    )

    # ----------------------------------------
    # RESULTADO
    # ----------------------------------------

    print()
    print("=" * 76)
    print("PREDICCIONES GENERADAS")
    print("=" * 76)

    print(
        f"Modelo       : "
        f"{info['metadata']['archivo_modelo']}"
    )

    print(
        f"Umbral       : "
        f"{info['umbral']:.12f}"
    )

    print(
        f"Filas        : "
        f"{len(info['resultado']):,}"
    )

    print(
        f"Contactar=1  : "
        f"{info['contactados']:,}"
    )

    print(
        f"Contactar=0  : "
        f"{len(info['resultado']) - info['contactados']:,}"
    )

    print(
        f"Score mínimo : "
        f"{info['resultado']['puntaje'].min():.6f}"
    )

    print(
        f"Score máximo : "
        f"{info['resultado']['puntaje'].max():.6f}"
    )

    print()
    print(
        f"CSV          : "
        f"{salida.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"SHA256 CSV   : "
        f"{info['sha256']}"
    )

    print(
        f"Manifest     : "
        f"{manifest.relative_to(PROJECT_ROOT)}"
    )

    print()
    print(
        "[OK] El modelo fue cargado "
        "desde disco."
    )

    print(
        "[OK] predecir.py NO "
        "reentrenó el modelo."
    )

    print(
        "[OK] Se respetó la fecha "
        "de corte solicitada."
    )

    print()
    print("=" * 76)
    print("PROCESO COMPLETADO")
    print("=" * 76)


if __name__ == "__main__":
    main()