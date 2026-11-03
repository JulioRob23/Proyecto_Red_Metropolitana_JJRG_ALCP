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

SOURCE_FILE = "transmetro_validaciones.csv"
SOURCE_PATH = PROJECT_ROOT / "datos" / "raw" / SOURCE_FILE

TOPIC = "redmetro.transmetro.validaciones"

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

CONFIRM_BATCH = 5000
ACK_TIMEOUT = 660

def calcular_sha256(ruta_archivo):
    """Calcula SHA-256 para identificar el archivo fuente."""

    sha256 = hashlib.sha256()

    with open(ruta_archivo, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()


def contar_registros(ruta_archivo):
    """Cuenta las filas del CSV sin incluir el encabezado."""

    with open(
        ruta_archivo,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as archivo:

        total_lineas = sum(1 for _ in archivo)

    return max(total_lineas - 1, 0)


def confirmar_lote(futuros):
    """
    Espera confirmación real de Kafka para cada mensaje
    del lote. Si alguno falla, el producer falla aquí
    y no continúa fingiendo que fue publicado.
    """

    for futuro in futuros:
        futuro.get(timeout=ACK_TIMEOUT)

def main():

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró: {SOURCE_PATH}"
        )

    total_esperado = contar_registros(SOURCE_PATH)
    hash_archivo = calcular_sha256(SOURCE_PATH)

    print("=" * 70)
    print("PRODUCER - TRANSMETRO")
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

        # Garantía de no duplicar mensajes ante retries
        enable_idempotence=True,
        acks="all",

        # Un solo request en vuelo conserva el orden.
        max_in_flight_requests_per_connection=1,

        # Kafka puede recuperarse de cambios temporales
        # de líder o reconexiones.
        retry_backoff_ms=1000,
        metadata_max_age_ms=10000,
        reconnect_backoff_ms=1000,
        reconnect_backoff_max_ms=10000,

        linger_ms=10,
        batch_size=65536,

        request_timeout_ms=60000,

        # Hasta 10 minutos para recuperarse de
        # errores temporales del broker.
        delivery_timeout_ms=600000,

        max_block_ms=120000
    )

    # --------------------------------------------------
    # Evento START
    # --------------------------------------------------

    producer.send(
        TOPIC,
        key=hash_archivo[:12],
        value={
            "_type": "START",
            "_source_file": SOURCE_FILE,
            "_source_sha256": hash_archivo,
            "_expected_rows": total_esperado
        }
    ).get(timeout=ACK_TIMEOUT)

    # --------------------------------------------------
    # Publicar CSV línea por línea
    # --------------------------------------------------
    
    futuros = []
    total_confirmado = 0
    
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

            futuro = producer.send(
                TOPIC,
                key=f"{hash_archivo[:12]}:{numero_fila}",
                value=evento
            )

            futuros.append(futuro)

            if len(futuros) >= CONFIRM_BATCH:

                confirmar_lote(futuros)

                total_confirmado += len(futuros)

                futuros = []

                print(
                    f"Confirmados por Kafka: "
                    f"{total_confirmado}/{total_esperado}"
                )
        
        if futuros:

            confirmar_lote(futuros)

            total_confirmado += len(futuros)

            print(
                f"Confirmados por Kafka: "
                f"{total_confirmado}/{total_esperado}"
            )

            futuros = []

    # --------------------------------------------------
    # Evento END
    # --------------------------------------------------

    producer.send(
        TOPIC,
        key=hash_archivo[:12],
        value={
            "_type": "END",
            "_source_file": SOURCE_FILE,
            "_source_sha256": hash_archivo,
            "_expected_rows": total_esperado
        }
    ).get(timeout=ACK_TIMEOUT)

    producer.flush()
    producer.close()

    print()
    print("=" * 70)
    print(
        f"[OK] Eventos confirmados por Kafka: "
        f"{total_confirmado}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()