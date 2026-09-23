from pathlib import Path
import csv
import hashlib
import json
import os

from kafka import KafkaProducer


# --------------------------------------------------
# Configuración
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_FILE = "aerometro_boardings.csv"
SOURCE_PATH = PROJECT_ROOT / "datos" / "raw" / SOURCE_FILE

TOPIC = "redmetro.aerometro.boardings"

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)


def calcular_sha256(ruta_archivo):

    sha256 = hashlib.sha256()

    with open(ruta_archivo, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()


def contar_registros(ruta_archivo):

    with open(
        ruta_archivo,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as archivo:

        total_lineas = sum(1 for _ in archivo)

    return max(total_lineas - 1, 0)


def main():

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró: {SOURCE_PATH}"
        )

    total_esperado = contar_registros(SOURCE_PATH)
    hash_archivo = calcular_sha256(SOURCE_PATH)

    print("=" * 70)
    print("PRODUCER - AERÓMETRO")
    print("=" * 70)

    print(f"Archivo: {SOURCE_FILE}")
    print(f"Eventos esperados: {total_esperado}")
    print(f"Topic: {TOPIC}")
    print()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda valor: json.dumps(
            valor,
            ensure_ascii=False
        ).encode("utf-8"),
        key_serializer=lambda clave: clave.encode("utf-8"),
        acks="all",
        retries=5,
        linger_ms=20,
        batch_size=65536
    )

    # Evento START
    producer.send(
        TOPIC,
        key=hash_archivo[:12],
        value={
            "_type": "START",
            "_source_file": SOURCE_FILE,
            "_source_sha256": hash_archivo,
            "_expected_rows": total_esperado
        }
    )

    # Eventos DATA
    with open(
        SOURCE_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as archivo:

        reader = csv.DictReader(archivo)

        for numero_fila, fila in enumerate(reader, start=1):

            evento = {
                "_type": "DATA",
                "_source_file": SOURCE_FILE,
                "_source_sha256": hash_archivo,
                "_row_number": numero_fila,
                "payload": fila
            }

            producer.send(
                TOPIC,
                key=f"{hash_archivo[:12]}:{numero_fila}",
                value=evento
            )

            if numero_fila % 50000 == 0:
                print(
                    f"Publicados: "
                    f"{numero_fila}/{total_esperado}"
                )

    # Evento END
    producer.send(
        TOPIC,
        key=hash_archivo[:12],
        value={
            "_type": "END",
            "_source_file": SOURCE_FILE,
            "_source_sha256": hash_archivo,
            "_expected_rows": total_esperado
        }
    )

    producer.flush()
    producer.close()

    print()
    print("=" * 70)
    print(f"[OK] Eventos publicados: {total_esperado}")
    print("=" * 70)


if __name__ == "__main__":
    main()