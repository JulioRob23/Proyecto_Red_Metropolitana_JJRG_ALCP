# Controles Técnicos de Seguridad

## Credenciales

- No versionar archivos `.env`.
- No almacenar contraseñas directamente en Git.
- Utilizar variables de entorno para configuraciones sensibles.
- Compartir únicamente archivos de ejemplo sin secretos.
- No guardar contraseñas en Tableau.

## Identificadores

Las capas de consumo analítico utilizan:

usuario_id
usuario_key


en lugar de identificadores operacionales originales.

Los identificadores de origen solo deben estar disponibles en capas donde
sean necesarios para integración y trazabilidad.

## Accesos

El acceso debe asignarse según la función del usuario y siguiendo el
principio de mínimo privilegio.

## Retención

El detalle individual se conserva por un máximo de 12 meses salvo excepción
autorizada.

Después de ese período debe eliminarse o anonimizarse cuando ya no sea
necesario.

## Auditoría

Los cambios de configuración, modelos y políticas deben permanecer
versionados mediante Git.

Los accesos excepcionales a datos individuales deben quedar justificados y
registrados.