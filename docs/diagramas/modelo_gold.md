# Modelo dimensional - Capa Gold

El modelo Gold está diseñado para analizar la demanda de transporte de la
red metropolitana y conservar adicionalmente el detalle completo de los
viajes de MetroRiel.

```mermaid
erDiagram

    DIM_USUARIO ||--o{ FACT_ABORDAJES : usuario
    DIM_MODO ||--o{ FACT_ABORDAJES : modo
    DIM_TIEMPO ||--o{ FACT_ABORDAJES : momento
    DIM_ZONA ||--o{ FACT_ABORDAJES : zona
    DIM_PUNTO_SERVICIO ||--o{ FACT_ABORDAJES : punto

    DIM_USUARIO ||--o{ FACT_VIAJES_METRORIEL : usuario
    DIM_MODO ||--o{ FACT_VIAJES_METRORIEL : modo

    DIM_TIEMPO ||--o{ FACT_VIAJES_METRORIEL : entrada
    DIM_TIEMPO ||--o{ FACT_VIAJES_METRORIEL : salida

    DIM_ZONA ||--o{ FACT_VIAJES_METRORIEL : origen
    DIM_ZONA ||--o{ FACT_VIAJES_METRORIEL : destino

    DIM_PUNTO_SERVICIO ||--o{ FACT_VIAJES_METRORIEL : origen
    DIM_PUNTO_SERVICIO ||--o{ FACT_VIAJES_METRORIEL : destino

    DIM_MODO ||--o{ DIM_PUNTO_SERVICIO : clasifica
    DIM_ZONA ||--o{ DIM_PUNTO_SERVICIO : ubica

    DIM_USUARIO {
        bigint usuario_key PK
        text usuario_id
        bigint cantidad_sistemas
        text sistemas_observados
        boolean es_multimodal_aprox
        boolean identidad_aislada
    }

    DIM_MODO {
        integer modo_key PK
        text modo_codigo
        text modo_nombre
    }

    DIM_TIEMPO {
        bigint tiempo_key PK
        timestamp minuto_inicio
        date fecha
        integer anio
        integer mes
        integer dia
        integer hora
        integer minuto
        integer numero_dia_semana
        text dia_semana
        boolean es_dia_habil
        boolean es_hora_pico
    }

    DIM_ZONA {
        integer zona_key PK
        text zona_nombre
    }

    DIM_PUNTO_SERVICIO {
        bigint punto_servicio_key PK
        integer modo_key FK
        text modo_codigo
        text codigo_fuente
        text nombre
        text linea_ruta_eje
        integer zona_key FK
        text zona_nombre
        numeric latitud
        numeric longitud
    }

    FACT_ABORDAJES {
        bigint abordaje_key PK
        bigint usuario_key FK
        integer modo_key FK
        bigint tiempo_key FK
        integer zona_key FK
        bigint punto_servicio_key FK
        text evento_id
        integer cantidad_abordajes
        numeric monto_gtq
    }

    FACT_VIAJES_METRORIEL {
        bigint viaje_key PK
        bigint trip_id
        bigint usuario_key FK
        integer modo_key FK
        bigint tiempo_entrada_key FK
        bigint tiempo_salida_key FK
        integer zona_origen_key FK
        integer zona_destino_key FK
        bigint punto_origen_key FK
        bigint punto_destino_key FK
        integer cantidad_viajes
        numeric tarifa_gtq
        integer duracion_segundos
    }
```

## Grano

**fact_abordajes:** una fila representa un abordaje válido de un usuario
en un modo, punto de servicio e instante determinado.

**fact_viajes_metroriel:** una fila representa un viaje completo válido
de MetroRiel desde una estación de origen hacia una estación de destino.