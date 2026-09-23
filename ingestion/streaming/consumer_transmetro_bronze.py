from pathlib import Path
from datetime import datetime
import json
import os

import pandas as pd
from kafka import KafkaConsumer


# --------------------------------------------------
# Configuración
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_SOURCE_DIR = (
    PROJECT_ROOT
    / "lake"
    / "bronze"
    / "transmetro"
)

TOPIC = "redmetro.transmetro.validaciones"

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

GROUP_ID = "redmetro-bronze-transmetro-v1"

CHUNK_SIZE = 50000


def guardar_chunk(
    registros,
    directorio_destino,
    hash_corto,
    numero_chunk
):
    """Guarda un bloque de registros en Parquet."""

    if not registros:
        return

    df = pd.DataFrame(registros)

    ruta_destino = (
        directorio_destino
        / f"part-{hash_corto}-{numero_chunk:05d}.parquet"
    )

    df.to_parquet(
        ruta_destino,
        index=False,
        engine="pyarrow"
    )

    print(
        f"  Chunk {numero_chunk}: "
        f"{len(df)} filas"
    )


def main():

    print("=" * 70)
    print("CONSUMER - TRANSMETRO -> BRONZE")
    print("=" * 70)
    print("Esperando eventos...")
    print()

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda valor: json.loads(
            valor.decode("utf-8")
        ),
        consumer_timeout_ms=600000
    )

    buffer = []

    hash_actual = None
    hash_corto = None
    archivo_actual = None

    fecha_hora_ingesta = None
    directorio_destino = None
    manifest_path = None

    total_recibido = 0
    total_esperado = None
    numero_chunk = 0

    omitir_corrida = False
    end_recibido = False

    for mensaje in consumer:

        evento = mensaje.value
        tipo = evento.get("_type")

        # --------------------------------------------------
        # START
        # --------------------------------------------------

        if tipo == "START":

            hash_actual = evento["_source_sha256"]
            hash_corto = hash_actual[:12]
            archivo_actual = evento["_source_file"]
            total_esperado = evento["_expected_rows"]

            manifest_dir = (
                BRONZE_SOURCE_DIR
                / "_manifests"
            )

            manifest_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            manifest_path = (
                manifest_dir
                / f"{hash_actual}.json"
            )

            # Si ya existe un manifiesto para el mismo
            # archivo, Bronze ya fue cargado previamente.
            if manifest_path.exists():

                omitir_corrida = True

                print(
                    "[INFO] El archivo ya fue procesado "
                    "anteriormente."
                )

                print(
                    "[INFO] Se consumirán los mensajes "
                    "sin duplicar Bronze."
                )

                continue

            omitir_corrida = False

            fecha_hora_ingesta = (
                datetime.now().astimezone()
            )

            fecha_ingesta = (
                fecha_hora_ingesta.date().isoformat()
            )

            directorio_destino = (
                BRONZE_SOURCE_DIR
                / f"ingestion_date={fecha_ingesta}"
            )

            directorio_destino.mkdir(
                parents=True,
                exist_ok=True
            )

            # Si existiera una carga incompleta previa,
            # eliminamos únicamente los chunks del mismo hash.
            for archivo in BRONZE_SOURCE_DIR.glob(
                f"ingestion_date=*/part-{hash_corto}-*.parquet"
            ):
                archivo.unlink()

            print(f"Archivo: {archivo_actual}")
            print(f"Filas esperadas: {total_esperado}")
            print(
                f"Partición: "
                f"ingestion_date={fecha_ingesta}"
            )
            print()

        # --------------------------------------------------
        # DATA
        # --------------------------------------------------

        elif tipo == "DATA":

            if omitir_corrida:
                continue

            if evento["_source_sha256"] != hash_actual:
                continue

            fila = dict(evento["payload"])

            fila["_row_number"] = evento["_row_number"]
            fila["_ingested_at"] = (
                fecha_hora_ingesta.isoformat()
            )
            fila["_source_file"] = archivo_actual
            fila["_source_sha256"] = hash_actual

            buffer.append(fila)

            total_recibido += 1

            if len(buffer) >= CHUNK_SIZE:

                numero_chunk += 1

                guardar_chunk(
                    buffer,
                    directorio_destino,
                    hash_corto,
                    numero_chunk
                )

                buffer = []

        # --------------------------------------------------
        # END
        # --------------------------------------------------

        elif tipo == "END":

            if evento["_source_sha256"] != hash_actual:
                continue

            if omitir_corrida:

                consumer.commit()
                end_recibido = True

                print()
                print("=" * 70)
                print(
                    "[OK] Archivo ya existente. "
                    "No se duplicaron registros."
                )
                print("=" * 70)

                break

            if buffer:

                numero_chunk += 1

                guardar_chunk(
                    buffer,
                    directorio_destino,
                    hash_corto,
                    numero_chunk
                )

                buffer = []

            if total_recibido != total_esperado:
                raise RuntimeError(
                    f"Conteo incorrecto. "
                    f"Esperados: {total_esperado}, "
                    f"recibidos: {total_recibido}"
                )

            manifest = {
                "source_file": archivo_actual,
                "source_sha256": hash_actual,
                "rows": total_recibido,
                "ingested_at": (
                    fecha_hora_ingesta.isoformat()
                ),
                "partition": str(
                    directorio_destino.relative_to(
                        PROJECT_ROOT
                    )
                )
            }

            with open(
                manifest_path,
                "w",
                encoding="utf-8"
            ) as archivo_manifest:

                json.dump(
                    manifest,
                    archivo_manifest,
                    indent=2,
                    ensure_ascii=False
                )

            consumer.commit()
            end_recibido = True

            print()
            print("=" * 70)
            print(
                f"[OK] Filas cargadas en Bronze: "
                f"{total_recibido}"
            )
            print(
                f"[OK] Archivos Parquet: "
                f"{numero_chunk}"
            )
            print("=" * 70)

            break

    consumer.close()

    if not end_recibido:
        raise RuntimeError(
            "El consumer terminó sin recibir "
            "el evento END."
        )


if __name__ == "__main__":
    main()