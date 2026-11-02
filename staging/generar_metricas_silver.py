from pathlib import Path
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# --------------------------------------------------
# Configuración
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "metricas"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def conectar():

    return psycopg2.connect(
        host=os.getenv(
            "POSTGRES_HOST",
            "localhost"
        ),
        port=int(
            os.getenv(
                "POSTGRES_PORT",
                "5433"
            )
        ),
        dbname=os.getenv(
            "POSTGRES_DB",
            "red_metropolitana"
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "red_user"
        ),
        password=os.getenv(
            "POSTGRES_PASSWORD"
        )
    )


def scalar(cursor, sql):

    cursor.execute(sql)

    return cursor.fetchone()[0]


def main():

    conn = conectar()
    cur = conn.cursor()

    metricas = []

    # ==================================================
    # FILAS VÁLIDAS EN SILVER
    # ==================================================

    tablas_silver = {
        "Transmetro":
            "silver.silver_transmetro_validaciones",

        "Transurbano":
            "silver.silver_transurbano_transacciones",

        "MetroRiel":
            "silver.silver_metroriel_viajes",

        "Aerometro":
            "silver.silver_aerometro_boardings",
    }

    filas_silver = {}

    for operador, tabla in tablas_silver.items():

        cantidad = scalar(
            cur,
            f"SELECT COUNT(*) FROM {tabla};"
        )

        filas_silver[operador] = cantidad

        metricas.append({
            "categoria": "Silver",
            "metrica": f"Filas válidas {operador}",
            "valor": cantidad,
            "porcentaje": None
        })

    total_silver = sum(
        filas_silver.values()
    )

    metricas.append({
        "categoria": "Silver",
        "metrica": "Total filas válidas Silver",
        "valor": total_silver,
        "porcentaje": None
    })

    # ==================================================
    # CUARENTENA POR FUENTE
    # ==================================================

    cur.execute(
        """
        SELECT
            fuente,
            COUNT(DISTINCT registro_id)

        FROM quarantine.registros_invalidos

        GROUP BY fuente;
        """
    )

    rechazados_por_fuente = {
        fuente: cantidad
        for fuente, cantidad in cur.fetchall()
    }

    # Total observado por operador =
    # válidos + registros únicos rechazados.

    total_fuente = {
        "TRANSMETRO":
            filas_silver["Transmetro"]
            + rechazados_por_fuente.get(
                "TRANSMETRO",
                0
            ),

        "TRANSURBANO":
            filas_silver["Transurbano"]
            + rechazados_por_fuente.get(
                "TRANSURBANO",
                0
            ),

        "METRORIEL":
            filas_silver["MetroRiel"]
            + rechazados_por_fuente.get(
                "METRORIEL",
                0
            ),

        "AEROMETRO":
            filas_silver["Aerometro"]
            + rechazados_por_fuente.get(
                "AEROMETRO",
                0
            ),
    }

    # ==================================================
    # INCUMPLIMIENTOS POR REGLA
    # ==================================================

    cur.execute(
        """
        SELECT
            regla_calidad,
            fuente,
            COUNT(*)

        FROM quarantine.registros_invalidos

        GROUP BY
            regla_calidad,
            fuente

        ORDER BY regla_calidad;
        """
    )

    for regla, fuente, cantidad in cur.fetchall():

        total_operador = total_fuente[
            fuente
        ]

        porcentaje = round(
            (
                cantidad
                / total_operador
            ) * 100,
            4
        )

        metricas.append({
            "categoria": "Calidad",
            "metrica": regla,
            "valor": cantidad,
            "porcentaje": porcentaje
        })

    # ==================================================
    # CUARENTENA TOTAL
    # ==================================================

    incumplimientos = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM quarantine.registros_invalidos;
        """
    )

    registros_unicos = scalar(
        cur,
        """
        SELECT COUNT(
            DISTINCT fuente || ':' || registro_id
        )
        FROM quarantine.registros_invalidos;
        """
    )

    total_operacional = (
        total_silver
        + registros_unicos
    )

    porcentaje_cuarentena = round(
        (
            registros_unicos
            / total_operacional
        ) * 100,
        4
    )

    metricas.append({
        "categoria": "Calidad",
        "metrica": "Incumplimientos totales",
        "valor": incumplimientos,
        "porcentaje": round(
            (
                incumplimientos
                / total_operacional
            ) * 100,
            4
        )
    })

    metricas.append({
        "categoria": "Calidad",
        "metrica": "Registros únicos en cuarentena",
        "valor": registros_unicos,
        "porcentaje": porcentaje_cuarentena
    })

    # ==================================================
    # IDENTIDAD
    # ==================================================

    llaves_fuente = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM silver.bridge_identidad_usuarios;
        """
    )

    usuarios_conformados = scalar(
        cur,
        """
        SELECT COUNT(DISTINCT usuario_id)
        FROM silver.bridge_identidad_usuarios;
        """
    )

    usuarios_multimodales = scalar(
        cur,
        """
        SELECT COUNT(*)

        FROM (

            SELECT usuario_id

            FROM silver.bridge_identidad_usuarios

            WHERE metodo_identidad
                = 'NUCLEO_NUMERICO'

            GROUP BY usuario_id

            HAVING COUNT(
                DISTINCT sistema
            ) >= 2

        ) x;
        """
    )

    metricas.extend([
        {
            "categoria": "Identidad",
            "metrica": "Llaves fuente",
            "valor": llaves_fuente,
            "porcentaje": None
        },
        {
            "categoria": "Identidad",
            "metrica": "Usuarios conformados",
            "valor": usuarios_conformados,
            "porcentaje": None
        },
        {
            "categoria": "Identidad",
            "metrica": "Usuarios multimodales aproximados",
            "valor": usuarios_multimodales,
            "porcentaje": None
        }
    ])

    # ==================================================
    # SCD TIPO 2
    # ==================================================

    versiones_scd = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM silver.scd2_padron_transmetro;
        """
    )

    tarjetas_scd = scalar(
        cur,
        """
        SELECT COUNT(DISTINCT tarjeta)
        FROM silver.scd2_padron_transmetro;
        """
    )

    activas_actuales = scalar(
        cur,
        """
        SELECT COUNT(*)

        FROM silver.scd2_padron_transmetro

        WHERE es_actual = true
          AND activo = true;
        """
    )

    inactivas_actuales = scalar(
        cur,
        """
        SELECT COUNT(*)

        FROM silver.scd2_padron_transmetro

        WHERE es_actual = true
          AND activo = false;
        """
    )

    metricas.extend([
        {
            "categoria": "SCD2",
            "metrica": "Versiones históricas",
            "valor": versiones_scd,
            "porcentaje": None
        },
        {
            "categoria": "SCD2",
            "metrica": "Tarjetas historizadas",
            "valor": tarjetas_scd,
            "porcentaje": None
        },
        {
            "categoria": "SCD2",
            "metrica": "Tarjetas activas actuales",
            "valor": activas_actuales,
            "porcentaje": None
        },
        {
            "categoria": "SCD2",
            "metrica": "Tarjetas inactivas actuales",
            "valor": inactivas_actuales,
            "porcentaje": None
        }
    ])

    # ==================================================
    # ZONAS
    # ==================================================

    zonas = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM silver.dim_zona_conformada;
        """
    )

    metricas.append({
        "categoria": "Integración",
        "metrica": "Zonas conformadas",
        "valor": zonas,
        "porcentaje": None
    })

    # ==================================================
    # GENERAR ENTREGABLES
    # ==================================================

    df = pd.DataFrame(metricas)

    df.to_csv(
        OUTPUT_DIR
        / "metricas_fase1_3.csv",
        index=False,
        encoding="utf-8-sig"
    )

    with open(
        OUTPUT_DIR
        / "metricas_fase1_3.md",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "# Métricas de Silver y calidad - Fase 1.3\n\n"
        )

        archivo.write(
            df.to_markdown(
                index=False
            )
        )

        archivo.write("\n")

    # ==================================================
    # MOSTRAR RESUMEN
    # ==================================================

    print("=" * 90)
    print("MÉTRICAS FASE 1.3")
    print("=" * 90)

    print(
        df.to_string(
            index=False
        )
    )

    print()
    print("-" * 90)

    print(
        f"Total operacional original : "
        f"{total_operacional}"
    )

    print(
        f"Total válido en Silver     : "
        f"{total_silver}"
    )

    print(
        f"Registros únicos cuarentena: "
        f"{registros_unicos}"
    )

    print(
        f"Incumplimientos detectados : "
        f"{incumplimientos}"
    )

    print(
        f"% registros en cuarentena  : "
        f"{porcentaje_cuarentena}%"
    )

    print("=" * 90)

    print()
    print(
        "[OK] Archivos generados:"
    )

    print(
        "docs/metricas/"
        "metricas_fase1_3.csv"
    )

    print(
        "docs/metricas/"
        "metricas_fase1_3.md"
    )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()