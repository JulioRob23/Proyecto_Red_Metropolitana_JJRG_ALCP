# Diagrama de Linaje

```mermaid
flowchart LR

    A[Fuentes operacionales] --> B[Ingesta Batch / Streaming / CDC]
    B --> C[Bronze - Parquet]
    C --> D[Staging operacional]
    D --> E[dbt Staging]
    E --> F[Silver]

    F --> Q[Cuarentena]
    F --> G[Gold]
    F --> H[Features]

    G --> I[Vistas analíticas Gold]
    I --> J[Tableau]
    J --> K[Recomendación]

    H --> L[Futuro ML]

