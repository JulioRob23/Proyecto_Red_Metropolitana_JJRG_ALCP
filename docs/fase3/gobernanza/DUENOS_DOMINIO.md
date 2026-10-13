# Dueños por Dominio de Datos

## Objetivo

La gobernanza requiere que cada dominio de información tenga un responsable
claramente definido.

El dueño del dominio no necesariamente ejecuta las transformaciones técnicas,
pero sí responde por el significado del dato y aprueba cambios en sus
definiciones oficiales.

Los siguientes roles se proponen para la Agencia Metropolitana.

---

## Matriz de responsabilidad

| Dominio | Dueño propuesto | Responsabilidad principal |
|---|---|---|
| Modos de transporte | Responsable de Operaciones | Aprobar códigos, nombres y cambios relacionados con los modos integrados. |
| Zonas | Responsable de Planeación Territorial | Aprobar nombres, equivalencias y cambios en la clasificación territorial. |
| Puntos de servicio | Responsable de Operaciones e Infraestructura | Mantener estaciones, paradas, rutas, líneas y ubicación de puntos de servicio. |
| Identidad de usuario | Responsable de Gobierno de Datos | Aprobar reglas de conformación, seudonimización y vinculación entre operadores. |
| Tiempo y calendario | Equipo de Plataforma de Datos | Mantener la dimensión temporal y reglas técnicas como día hábil y hora pico una vez aprobadas. |
| Calidad de datos | Equipo de Plataforma de Datos | Implementar y monitorear las reglas de validación, cuarentena y reconciliación. |
| Métricas analíticas | Responsable de Gobierno de Datos | Aprobar las definiciones utilizadas en Gold, Tableau y reportes oficiales. |
| Seguridad y privacidad | Responsable de Seguridad de Información | Autorizar niveles de acceso, tratamiento de datos personales y políticas de retención. |

---

# Responsabilidades

## Dueño del dominio

El dueño del dominio:

- define el significado oficial de los datos;
- revisa solicitudes de cambio;
- aprueba modificaciones que afecten métricas o interpretación;
- asegura que los distintos operadores utilicen una definición común.

## Equipo de Plataforma de Datos

El equipo técnico:

- implementa las reglas aprobadas;
- mantiene los modelos dbt;
- ejecuta pruebas de calidad;
- conserva trazabilidad y linaje;
- no modifica unilateralmente definiciones de negocio.

## Consumidores analíticos

Los analistas y usuarios de Tableau:

- utilizan las definiciones oficiales;
- no deben redefinir métricas de forma independiente;
- reportan inconsistencias al dueño correspondiente.

---

# Proceso de cambio

Cuando se solicita modificar una definición:

1. Se documenta la necesidad del cambio.
2. El dueño del dominio evalúa el impacto.
3. Se revisa el efecto sobre Silver, Gold, Tableau y features.
4. El dueño aprueba o rechaza la modificación.
5. El equipo de datos implementa el cambio.
6. Se actualizan pruebas y documentación.
7. El cambio queda registrado mediante Git.

---

# Ejemplo

Si se decide cambiar la definición de una zona:

- Planeación Territorial aprueba la nueva definición.
- Plataforma de Datos modifica la normalización correspondiente.
- Se revisa `dim_zona` y cualquier modelo dependiente.
- Se ejecutan pruebas dbt.
- Se actualizan Tableau y documentación si existe impacto.
- El cambio queda registrado mediante un commit.

De esta forma una definición institucional no depende de la decisión
individual de un analista o desarrollador.