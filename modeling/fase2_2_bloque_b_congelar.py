from pathlib import Path
import json

import pandas as pd


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FASE2_DIR = (
    PROJECT_ROOT
    / "docs"
    / "proyecto2"
    / "fase2"
)

UMBRAL_PATH = (
    FASE2_DIR
    / "fase2_2_umbral_resumen.csv"
)

ENSEMBLE_PATH = (
    FASE2_DIR
    / "fase2_1_ensemble_resumen.csv"
)

CONFIG_PATH = (
    PROJECT_ROOT
    / "modeling"
    / "fase2_2_config_modelo_congelado.json"
)

DOC_PATH = (
    FASE2_DIR
    / "fase2_2_pretest_b.md"
)


# ============================================================
# CONFIGURACIÓN DEFINITIVA DEL MODELO
# ============================================================

MODELO = "HistGradientBoostingClassifier"

PARAMETROS = {
    "learning_rate": 0.05,
    "max_iter": 150,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 30,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 42,
}


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
# LEER UMBRAL SELECCIONADO
# ============================================================

def cargar_umbral():

    if not UMBRAL_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_2_umbral_resumen.csv"
        )

    df = pd.read_csv(
        UMBRAL_PATH
    )

    fila = (
        df[
            df["tipo"]
            == "OOF óptimo"
        ]
    )

    if len(fila) != 1:

        raise RuntimeError(
            "No se encontró exactamente "
            "un umbral OOF óptimo."
        )

    return fila.iloc[0]


# ============================================================
# LEER RESULTADO DEL ENSEMBLE
# ============================================================

def cargar_ensemble():

    if not ENSEMBLE_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_1_ensemble_resumen.csv"
        )

    df = pd.read_csv(
        ENSEMBLE_PATH
    )

    if len(df) != 1:

        raise RuntimeError(
            "El resumen del ensemble "
            "debe contener una fila."
        )

    return df.iloc[0]


# ============================================================
# CREAR CONFIGURACIÓN
# ============================================================

def crear_configuracion(
    umbral,
    ensemble,
):

    return {
        "version":
            "p2_hgb_v1",

        "estado":
            "CONGELADO_ANTES_TEST_B",

        "modelo": {
            "clase":
                MODELO,

            "parametros":
                PARAMETROS,
        },

        "datos_entrenamiento": {
            "corte":
                "A",

            "fecha_corte":
                "2026-07-01",

            "filas":
                59999,

            "positivos":
                8310,

            "folds_cv":
                5,
        },

        "metrica_seleccion": {
            "nombre":
                "average_precision",

            "ap_validacion_media":
                float(
                    ensemble[
                        "ap_validacion_media"
                    ]
                ),

            "ap_validacion_std":
                float(
                    ensemble[
                        "ap_validacion_std"
                    ]
                ),
        },

        "umbral": {
            "metodo":
                "maxima_ganancia_OOF_corte_A",

            "valor":
                float(
                    umbral["umbral"]
                ),

            "teorico":
                5.0 / 15.0,

            "contactados_oof":
                int(
                    umbral["contactados"]
                ),

            "precision_oof":
                float(
                    umbral["precision"]
                ),

            "recall_oof":
                float(
                    umbral["recall"]
                ),

            "ganancia_oof_q":
                float(
                    umbral["ganancia_q"]
                ),
        },

        "escenario_economico": {
            "costo_contacto_q":
                5.0,

            "probabilidad_retencion":
                0.25,

            "valor_usuario_retenido_q":
                60.0,

            "beneficio_esperado_por_churner_contactado_q":
                15.0,
        },

        "features": FEATURES,

        "restricciones": [
            (
                "La etiqueta del corte B "
                "no se utilizó para seleccionar "
                "el modelo."
            ),
            (
                "La etiqueta del corte B "
                "no se utilizó para seleccionar "
                "el umbral."
            ),
            (
                "Después de evaluar B no se "
                "modificarán modelo, features, "
                "hiperparámetros ni umbral."
            ),
        ],
    }


# ============================================================
# DOCUMENTACIÓN PRE-TEST
# ============================================================

def crear_documentacion(
    config
):

    umbral = config["umbral"]
    metrica = config[
        "metrica_seleccion"
    ]

    texto = f"""# Fase 2.2 - Estado congelado antes del test B

## Estado

**B NO EVALUADO**

En este punto el modelo, sus hiperparámetros y el umbral se encuentran
congelados utilizando únicamente información del corte A.

## Modelo seleccionado

- Modelo: {config["modelo"]["clase"]}
- Versión: {config["version"]}
- learning_rate: {PARAMETROS["learning_rate"]}
- max_iter: {PARAMETROS["max_iter"]}
- max_leaf_nodes: {PARAMETROS["max_leaf_nodes"]}
- min_samples_leaf: {PARAMETROS["min_samples_leaf"]}
- l2_regularization: {PARAMETROS["l2_regularization"]}
- early_stopping: {PARAMETROS["early_stopping"]}
- random_state: {PARAMETROS["random_state"]}

## Rendimiento de validación

- Métrica: Average Precision
- AP media: {metrica["ap_validacion_media"]:.6f}
- AP std: {metrica["ap_validacion_std"]:.6f}
- Validación cruzada: 5 folds del corte A

## Escenario económico

- Costo por contacto: Q5
- Retención si la persona iba a abandonar: 25%
- Valor de una persona retenida: Q60
- Beneficio esperado de contactar a una persona que iba a abandonar: Q15

La ganancia para un grupo contactado se calcula como:

`Ganancia = 15 × TP - 5 × (TP + FP)`

## Umbral

El umbral económico teórico fue:

`5 / 15 = 0.333333`

El umbral seleccionado mediante las predicciones OOF del corte A fue:

**{umbral["valor"]:.6f}**

Con este umbral en A:

- Contactados: {umbral["contactados_oof"]:,}
- Precision: {umbral["precision_oof"]:.4f}
- Recall: {umbral["recall_oof"]:.4f}
- Ganancia esperada: Q{umbral["ganancia_oof_q"]:,.2f}

## Regla para el test

A partir de este punto no se modificarán las features, el modelo,
los hiperparámetros ni el umbral después de observar el resultado
del corte B.

La siguiente evaluación de B será la única evaluación de test del proyecto.
"""

    DOC_PATH.write_text(
        texto,
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("FASE 2.2 - BLOQUE B")
    print("CONGELAMIENTO PREVIO AL TEST B")
    print("=" * 72)

    umbral = cargar_umbral()

    ensemble = cargar_ensemble()

    config = crear_configuracion(
        umbral,
        ensemble,
    )

    with open(
        CONFIG_PATH,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            config,
            archivo,
            indent=2,
            ensure_ascii=False,
        )

    crear_documentacion(
        config
    )

    print()
    print("MODELO CONGELADO")
    print("-" * 72)

    print(
        f"Modelo       : "
        f"{config['modelo']['clase']}"
    )

    print(
        f"Versión      : "
        f"{config['version']}"
    )

    print(
        f"AP CV        : "
        f"{config['metrica_seleccion']['ap_validacion_media']:.6f}"
        " ± "
        f"{config['metrica_seleccion']['ap_validacion_std']:.6f}"
    )

    print(
        f"Umbral       : "
        f"{config['umbral']['valor']:.6f}"
    )

    print(
        f"Ganancia OOF : "
        f"Q{config['umbral']['ganancia_oof_q']:,.2f}"
    )

    print()
    print("ARCHIVOS")
    print("-" * 72)

    print(
        "[OK] "
        + str(
            CONFIG_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "[OK] "
        + str(
            DOC_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print("=" * 72)
    print("ESTADO: B NO EVALUADO")
    print("=" * 72)

    print(
        "[OK] Modelo congelado."
    )

    print(
        "[OK] Hiperparámetros congelados."
    )

    print(
        "[OK] Features congeladas."
    )

    print(
        "[OK] Umbral congelado."
    )

    print(
        "[OK] Listo para crear el "
        "commit pre-test."
    )


if __name__ == "__main__":
    main()