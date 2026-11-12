from pathlib import Path

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

PERFILES_PATH = (
    FASE2_DIR
    / "fase2_3_perfiles_compactos.csv"
)

SALIDA_CSV = (
    FASE2_DIR
    / "fase2_3_segmentos_final.csv"
)

SALIDA_MD = (
    FASE2_DIR
    / "fase2_3_segmentacion_kmeans_pca.md"
)


# ============================================================
# INTERPRETACIÓN DE SEGMENTOS
# ============================================================

SEGMENTOS = {

    1: {
        "nombre":
            "Usuarios principalmente MetroRiel",

        "prioridad_retencion":
            "Media",

        "accion":
            (
                "Mantener comunicación de continuidad "
                "y beneficios relacionados con MetroRiel, "
                "especialmente cuando empiece a aumentar "
                "el tiempo desde el último viaje."
            ),
    },

    2: {
        "nombre":
            "Usuarios principalmente Transurbano",

        "prioridad_retencion":
            "Alta",

        "accion":
            (
                "Priorizar campañas de retención con "
                "recordatorios y recargas de cortesía, "
                "porque es el segmento más grande y "
                "presenta la mayor tasa de abandono."
            ),
    },

    3: {
        "nombre":
            "Usuarios intensivos y muy activos",

        "prioridad_retencion":
            "Baja",

        "accion":
            (
                "No priorizar incentivos costosos de "
                "retención. Mantener seguimiento y "
                "beneficios de fidelización, ya que "
                "presentan una actividad muy alta y "
                "una tasa de abandono muy baja."
            ),
    },

    4: {
        "nombre":
            "Usuarios ocasionales de Aerómetro",

        "prioridad_retencion":
            "Media-Alta",

        "accion":
            (
                "Enviar campañas de reactivación e "
                "incentivos para volver a utilizar la "
                "red, considerando que presentan menor "
                "frecuencia y más días desde el último viaje."
            ),
    },

    5: {
        "nombre":
            "Usuarios principalmente Transmetro",

        "prioridad_retencion":
            "Media",

        "accion":
            (
                "Utilizar recordatorios o promociones "
                "de continuidad en Transmetro cuando "
                "se detecte una reducción reciente "
                "en su actividad."
            ),
    },
}


# ============================================================
# CARGAR
# ============================================================

def cargar_perfiles():

    if not PERFILES_PATH.exists():

        raise FileNotFoundError(
            "No se encontró "
            "fase2_3_perfiles_compactos.csv"
        )

    df = pd.read_csv(
        PERFILES_PATH
    )

    segmentos = set(
        df["segmento"]
        .astype(int)
        .tolist()
    )

    if segmentos != {
        1, 2, 3, 4, 5
    }:

        raise RuntimeError(
            "Se esperaban exactamente "
            "los segmentos 1 a 5."
        )

    return df


# ============================================================
# AGREGAR NOMBRES Y ACCIONES
# ============================================================

def enriquecer(
    df
):

    df = df.copy()

    df["nombre"] = (
        df["segmento"]
        .map(
            lambda x:
            SEGMENTOS[int(x)][
                "nombre"
            ]
        )
    )

    df[
        "prioridad_retencion"
    ] = (
        df["segmento"]
        .map(
            lambda x:
            SEGMENTOS[int(x)][
                "prioridad_retencion"
            ]
        )
    )

    df["accion"] = (
        df["segmento"]
        .map(
            lambda x:
            SEGMENTOS[int(x)][
                "accion"
            ]
        )
    )

    return df


# ============================================================
# DOCUMENTACIÓN
# ============================================================

def crear_documentacion(
    df
):

    filas = []

    for _, row in (
        df
        .sort_values(
            "segmento"
        )
        .iterrows()
    ):

        filas.append(
            f"""
### Segmento {int(row['segmento'])} - {row['nombre']}

- Tamaño: {int(row['tamanio']):,} personas
- Proporción de la población: {row['proporcion_poblacion'] * 100:.2f}%
- Tasa de abandono: {row['tasa_abandono'] * 100:.2f}%
- Viajes en 7 días: {row['mediana_viajes_7d']:.0f}
- Viajes en 14 días: {row['mediana_viajes_14d']:.0f}
- Viajes en 28 días: {row['mediana_viajes_28d']:.0f}
- Días activos en 28 días: {row['mediana_dias_activos_28d']:.0f}
- Días desde el último viaje: {row['mediana_dias_desde_ultimo_viaje']:.2f}
- Modos utilizados: {row['mediana_cantidad_modos_28d']:.0f}
- Gasto total mediano: Q{row['mediana_gasto_total_28d']:.2f}
- Modo predominante: {row['modo_mas_usado_moda']}
- Zona más frecuente: {row['zona_mas_frecuente_moda']}
- Prioridad de retención: {row['prioridad_retencion']}

**Acción propuesta:** {row['accion']}
"""
        )

    texto = f"""# Fase 2.3 - Segmentación con KMeans y PCA

## Preparación

Se utilizó únicamente la tabla de features del corte A.

Las variables numéricas fueron estandarizadas mediante StandardScaler y las
variables categóricas fueron codificadas mediante One-Hot Encoding.

La etiqueta de abandono no fue utilizada para formar los segmentos.

## Elección de k

Se evaluaron valores de k entre 2 y 8 utilizando dos criterios:

- método del codo mediante la inercia;
- silhouette score.

El mayor silhouette se obtuvo con k = 5 y el método del codo mostró una
reducción progresivamente menor de la inercia alrededor de cinco o seis
clusters.

Por esta razón se seleccionaron cinco segmentos.

## PCA

La visualización se realizó mediante PCA con dos componentes:

- PC1: 27.60% de varianza explicada
- PC2: 19.59% de varianza explicada
- Total: 47.19%

La proyección sirve para visualizar los grupos, pero KMeans fue ajustado con
las 34 dimensiones transformadas y no solamente con las dos dimensiones del
PCA.

## Perfiles de los segmentos

{''.join(filas)}

## Interpretación general

El segmento 2 tiene la mayor tasa de abandono (15.27%) y además representa
la mayor parte de la población, por lo que constituye un grupo importante
para las campañas de retención.

El segmento 3 presenta un comportamiento claramente diferente. Sus usuarios
realizan muchos más viajes, tienen más días activos y registran viajes muy
cerca de la fecha de corte. Su tasa de abandono es solamente 1.49%, por lo
que no sería eficiente priorizar incentivos costosos de retención en este
grupo.

Las tasas de abandono por segmento son descriptivas. La pertenencia a un
segmento no demuestra que el segmento sea la causa del abandono.
"""

    SALIDA_MD.write_text(
        texto,
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("FASE 2.3 - BLOQUE E")
    print("INTERPRETACIÓN FINAL DE SEGMENTOS")
    print("=" * 80)

    df = cargar_perfiles()

    final = enriquecer(
        df
    )

    final.to_csv(
        SALIDA_CSV,
        index=False
    )

    crear_documentacion(
        final
    )

    print()
    print("=" * 80)
    print("TABLA FINAL DE SEGMENTOS")
    print("=" * 80)

    columnas = [
        "segmento",
        "nombre",
        "tamanio",
        "tasa_abandono",
        "mediana_viajes_28d",
        "mediana_dias_activos_28d",
        "mediana_dias_desde_ultimo_viaje",
        "modo_mas_usado_moda",
        "prioridad_retencion",
    ]

    print(
        final[
            columnas
        ]
        .sort_values(
            "segmento"
        )
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 80)
    print("ACCIONES PROPUESTAS")
    print("=" * 80)

    for _, row in (
        final
        .sort_values(
            "segmento"
        )
        .iterrows()
    ):

        print()
        print(
            f"Segmento "
            f"{int(row['segmento'])} - "
            f"{row['nombre']}"
        )

        print(
            f"Prioridad: "
            f"{row['prioridad_retencion']}"
        )

        print(
            f"Acción: "
            f"{row['accion']}"
        )

    print()
    print("=" * 80)
    print("ARCHIVOS GENERADOS")
    print("=" * 80)

    print(
        "[OK] "
        + str(
            SALIDA_CSV.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "[OK] "
        + str(
            SALIDA_MD.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print("=" * 80)
    print("FASE 2.3 COMPLETADA")
    print("=" * 80)

    print(
        "[OK] Cinco segmentos nombrados."
    )

    print(
        "[OK] Segmentos descritos "
        "mediante medianas."
    )

    print(
        "[OK] Acciones de retención "
        "definidas."
    )

    print(
        "[OK] Tasa de abandono tratada "
        "solo como información descriptiva."
    )


if __name__ == "__main__":
    main()