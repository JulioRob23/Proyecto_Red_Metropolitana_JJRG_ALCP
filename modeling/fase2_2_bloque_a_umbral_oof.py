from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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

OOF_PATH = (
    FASE2_DIR
    / "fase2_1_ensemble_oof.csv"
)


# ============================================================
# CONSTANTES DEL ESCENARIO ECONÓMICO
# ============================================================

COSTO_CONTACTO = 5.0
PROB_RETENCION = 0.25
VALOR_RETENIDO = 60.0

BENEFICIO_ESPERADO_CHURNER = (
    PROB_RETENCION
    * VALOR_RETENIDO
)

UMBRAL_TEORICO = (
    COSTO_CONTACTO
    / BENEFICIO_ESPERADO_CHURNER
)


# ============================================================
# CONSTANTES DE CONTROL
# ============================================================

FILAS_ESPERADAS = 59999
POSITIVOS_ESPERADOS = 8310
FOLDS_ESPERADOS = 5


# ============================================================
# CARGAR Y VALIDAR OOF
# ============================================================

def cargar_oof():

    if not OOF_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_1_ensemble_oof.csv"
        )

    df = pd.read_csv(
        OOF_PATH
    )

    columnas_requeridas = {
        "unidad_id",
        "fold",
        "etiqueta",
        "modelo",
        "probabilidad",
    }

    faltantes = (
        columnas_requeridas
        - set(df.columns)
    )

    if faltantes:

        raise RuntimeError(
            "Faltan columnas en OOF: "
            + ", ".join(
                sorted(faltantes)
            )
        )

    if len(df) != FILAS_ESPERADAS:

        raise RuntimeError(
            f"Se esperaban {FILAS_ESPERADAS:,} "
            f"filas y llegaron {len(df):,}."
        )

    if (
        df["unidad_id"]
        .duplicated()
        .sum()
        != 0
    ):

        raise RuntimeError(
            "Hay unidades duplicadas "
            "en las predicciones OOF."
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
        df["fold"].nunique()
        != FOLDS_ESPERADOS
    ):

        raise RuntimeError(
            "No están los cinco folds."
        )

    modelos = (
        df["modelo"]
        .dropna()
        .unique()
    )

    if len(modelos) != 1:

        raise RuntimeError(
            "El archivo OOF debe contener "
            "un solo modelo."
        )

    if (
        df["probabilidad"]
        .isna()
        .any()
    ):

        raise RuntimeError(
            "Hay probabilidades nulas."
        )

    if not (
        df["probabilidad"]
        .between(
            0,
            1
        )
        .all()
    ):

        raise RuntimeError(
            "Hay probabilidades fuera "
            "del rango [0, 1]."
        )

    df["etiqueta"] = (
        df["etiqueta"]
        .astype(int)
    )

    return df


# ============================================================
# MÉTRICAS PARA UN UMBRAL
# ============================================================

def calcular_metricas_umbral(
    df,
    umbral,
):

    pred = (
        df["probabilidad"]
        >= umbral
    ).astype(int)

    y = df["etiqueta"]

    tp = int(
        (
            (pred == 1)
            & (y == 1)
        ).sum()
    )

    fp = int(
        (
            (pred == 1)
            & (y == 0)
        ).sum()
    )

    tn = int(
        (
            (pred == 0)
            & (y == 0)
        ).sum()
    )

    fn = int(
        (
            (pred == 0)
            & (y == 1)
        ).sum()
    )

    contactados = (
        tp
        + fp
    )

    precision = (
        tp / contactados
        if contactados > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    costo_total = (
        contactados
        * COSTO_CONTACTO
    )

    beneficio_esperado = (
        tp
        * BENEFICIO_ESPERADO_CHURNER
    )

    ganancia = (
        beneficio_esperado
        - costo_total
    )

    retenidos_esperados = (
        tp
        * PROB_RETENCION
    )

    return {
        "umbral": float(umbral),
        "contactados": int(contactados),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": float(precision),
        "recall": float(recall),
        "retenidos_esperados":
            float(retenidos_esperados),
        "costo_total_q":
            float(costo_total),
        "beneficio_esperado_q":
            float(beneficio_esperado),
        "ganancia_q":
            float(ganancia),
    }


# ============================================================
# CURVA EXACTA DE GANANCIA
# ============================================================

def construir_curva_exacta(
    df
):

    # Agrupamos por score para manejar correctamente
    # posibles probabilidades repetidas.
    agrupado = (
        df
        .groupby(
            "probabilidad",
            as_index=False
        )
        .agg(
            positivos=(
                "etiqueta",
                "sum"
            ),
            personas=(
                "unidad_id",
                "count"
            ),
        )
        .sort_values(
            "probabilidad",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    agrupado["negativos"] = (
        agrupado["personas"]
        - agrupado["positivos"]
    )

    # Al bajar el umbral acumulamos
    # todas las personas con score >= threshold.
    agrupado["tp"] = (
        agrupado["positivos"]
        .cumsum()
    )

    agrupado["fp"] = (
        agrupado["negativos"]
        .cumsum()
    )

    agrupado["contactados"] = (
        agrupado["personas"]
        .cumsum()
    )

    agrupado["fn"] = (
        POSITIVOS_ESPERADOS
        - agrupado["tp"]
    )

    negativos_totales = (
        FILAS_ESPERADAS
        - POSITIVOS_ESPERADOS
    )

    agrupado["tn"] = (
        negativos_totales
        - agrupado["fp"]
    )

    agrupado["precision"] = (
        agrupado["tp"]
        / agrupado["contactados"]
    )

    agrupado["recall"] = (
        agrupado["tp"]
        / POSITIVOS_ESPERADOS
    )

    agrupado[
        "retenidos_esperados"
    ] = (
        agrupado["tp"]
        * PROB_RETENCION
    )

    agrupado[
        "costo_total_q"
    ] = (
        agrupado["contactados"]
        * COSTO_CONTACTO
    )

    agrupado[
        "beneficio_esperado_q"
    ] = (
        agrupado["tp"]
        * BENEFICIO_ESPERADO_CHURNER
    )

    agrupado["ganancia_q"] = (
        agrupado[
            "beneficio_esperado_q"
        ]
        -
        agrupado[
            "costo_total_q"
        ]
    )

    agrupado = agrupado.rename(
        columns={
            "probabilidad":
                "umbral"
        }
    )

    return agrupado


# ============================================================
# ELEGIR UMBRAL
# ============================================================

def elegir_umbral_optimo(
    curva
):

    ganancia_maxima = (
        curva["ganancia_q"]
        .max()
    )

    candidatos = (
        curva[
            np.isclose(
                curva["ganancia_q"],
                ganancia_maxima
            )
        ]
        .copy()
    )

    # Si varios umbrales producen exactamente
    # la misma ganancia, elegimos el más alto:
    # misma ganancia contactando menos personas.
    mejor = (
        candidatos
        .sort_values(
            "umbral",
            ascending=False
        )
        .iloc[0]
    )

    return mejor


# ============================================================
# GRÁFICA
# ============================================================

def crear_grafica(
    curva,
    mejor,
    teorico,
):

    grafica = (
        curva[
            [
                "umbral",
                "ganancia_q",
            ]
        ]
        .sort_values(
            "umbral"
        )
    )

    figura = plt.figure(
        figsize=(10, 6)
    )

    plt.plot(
        grafica["umbral"],
        grafica["ganancia_q"],
        label="Ganancia OOF corte A",
    )

    plt.axvline(
        x=float(mejor["umbral"]),
        linestyle="--",
        label=(
            "Umbral OOF óptimo = "
            f"{mejor['umbral']:.4f}"
        ),
    )

    plt.axvline(
        x=UMBRAL_TEORICO,
        linestyle=":",
        label=(
            "Umbral económico teórico = "
            f"{UMBRAL_TEORICO:.4f}"
        ),
    )

    plt.scatter(
        [
            float(
                mejor["umbral"]
            )
        ],
        [
            float(
                mejor["ganancia_q"]
            )
        ],
        zorder=5,
    )

    plt.xlabel(
        "Umbral de probabilidad"
    )

    plt.ylabel(
        "Ganancia esperada (Q)"
    )

    plt.title(
        "Ganancia esperada vs umbral "
        "- predicciones OOF del corte A"
    )

    plt.legend()

    plt.grid(
        True,
        alpha=0.25
    )

    plt.tight_layout()

    ruta = (
        FASE2_DIR
        / "fase2_2_ganancia_vs_umbral.png"
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
    print("FASE 2.2 - BLOQUE A")
    print("UMBRAL SEGÚN COSTO CON PREDICCIONES OOF DE A")
    print("=" * 72)

    print()
    print("ESCENARIO ECONÓMICO")
    print("-" * 72)

    print(
        f"Costo por contacto       : "
        f"Q{COSTO_CONTACTO:.2f}"
    )

    print(
        f"Probabilidad de retención: "
        f"{PROB_RETENCION:.0%}"
    )

    print(
        f"Valor usuario retenido   : "
        f"Q{VALOR_RETENIDO:.2f}"
    )

    print(
        f"Beneficio esperado churner: "
        f"Q{BENEFICIO_ESPERADO_CHURNER:.2f}"
    )

    print()
    print(
        "Ganancia esperada individual:"
    )

    print(
        "  G(p) = 0.25 × 60 × p - 5"
    )

    print(
        "  G(p) = 15p - 5"
    )

    print()

    print(
        "Umbral económico teórico:"
    )

    print(
        f"  p = 5 / 15 = "
        f"{UMBRAL_TEORICO:.6f}"
    )

    # ----------------------------------------
    # OOF
    # ----------------------------------------

    df = cargar_oof()

    print()
    print("=" * 72)
    print("VALIDACIÓN DEL ARCHIVO OOF")
    print("=" * 72)

    print(
        f"Filas       : {len(df):,}"
    )

    print(
        f"Positivos   : "
        f"{df['etiqueta'].sum():,}"
    )

    print(
        f"Folds       : "
        f"{df['fold'].nunique()}"
    )

    print(
        f"Modelo      : "
        f"{df['modelo'].iloc[0]}"
    )

    print(
        "[OK] Cada unidad tiene "
        "una única predicción OOF."
    )

    print(
        "[OK] No se utilizó corte B."
    )

    # ----------------------------------------
    # Curva exacta
    # ----------------------------------------

    curva = construir_curva_exacta(
        df
    )

    mejor = elegir_umbral_optimo(
        curva
    )

    # Métricas exactamente en 1/3
    teorico = calcular_metricas_umbral(
        df,
        UMBRAL_TEORICO
    )

    # Recalcular explícitamente las métricas
    # del threshold elegido.
    optimo = calcular_metricas_umbral(
        df,
        float(mejor["umbral"])
    )

    # ----------------------------------------
    # Comparación
    # ----------------------------------------

    comparacion = pd.DataFrame([
        {
            "tipo":
                "Teórico",
            **teorico,
        },
        {
            "tipo":
                "OOF óptimo",
            **optimo,
        },
    ])

    ruta_curva_csv = (
        FASE2_DIR
        / "fase2_2_curva_ganancia.csv"
    )

    ruta_resumen = (
        FASE2_DIR
        / "fase2_2_umbral_resumen.csv"
    )

    curva.to_csv(
        ruta_curva_csv,
        index=False
    )

    comparacion.to_csv(
        ruta_resumen,
        index=False
    )

    ruta_grafica = crear_grafica(
        curva,
        mejor,
        teorico,
    )

    # ----------------------------------------
    # Resultados
    # ----------------------------------------

    print()
    print("=" * 72)
    print("COMPARACIÓN DE UMBRALES")
    print("=" * 72)

    columnas_mostrar = [
        "tipo",
        "umbral",
        "contactados",
        "tp",
        "fp",
        "precision",
        "recall",
        "ganancia_q",
    ]

    print(
        comparacion[
            columnas_mostrar
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 72)
    print("UMBRAL SELECCIONADO CON OOF DE A")
    print("=" * 72)

    print(
        f"Umbral               : "
        f"{optimo['umbral']:.6f}"
    )

    print(
        f"Contactados           : "
        f"{optimo['contactados']:,}"
    )

    print(
        f"TP                    : "
        f"{optimo['tp']:,}"
    )

    print(
        f"FP                    : "
        f"{optimo['fp']:,}"
    )

    print(
        f"TN                    : "
        f"{optimo['tn']:,}"
    )

    print(
        f"FN                    : "
        f"{optimo['fn']:,}"
    )

    print(
        f"Precision             : "
        f"{optimo['precision']:.4f}"
    )

    print(
        f"Recall                : "
        f"{optimo['recall']:.4f}"
    )

    print(
        f"Retenidos esperados   : "
        f"{optimo['retenidos_esperados']:.2f}"
    )

    print(
        f"Costo total           : "
        f"Q{optimo['costo_total_q']:,.2f}"
    )

    print(
        f"Beneficio esperado    : "
        f"Q{optimo['beneficio_esperado_q']:,.2f}"
    )

    print(
        f"GANANCIA ESPERADA     : "
        f"Q{optimo['ganancia_q']:,.2f}"
    )

    print()
    print("=" * 72)
    print("ARCHIVOS GENERADOS")
    print("=" * 72)

    for ruta in [
        ruta_curva_csv,
        ruta_resumen,
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
    print("BLOQUE A COMPLETADO")
    print("=" * 72)

    print(
        "[OK] Umbral seleccionado "
        "únicamente con OOF de A."
    )

    print(
        "[OK] Corte B sigue sin ser utilizado."
    )


if __name__ == "__main__":
    main()