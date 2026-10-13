# Guía de Ejecución Reproducible

## Objetivo

Esta guía describe los pasos necesarios para levantar y validar el proyecto
Red Metropolitana desde Visual Studio Code utilizando PowerShell.

---

## 1. Abrir el proyecto

Abrir la carpeta:


Proyecto_Red_Metropolitana


en Visual Studio Code.

La terminal debe estar ubicada en la raíz del proyecto.

---

## 2. Activar el entorno virtual

Ejecutar:

powershell
.\.venv\Scripts\Activate.ps1


La terminal debe mostrar:


(.venv)


Verificar Python:

powershell
python --version


Versión utilizada durante el desarrollo:


Python 3.11.9


---

## 3. Configurar dbt

En cada nueva sesión de PowerShell ejecutar:

powershell
$env:DBT_PROFILES_DIR = (Resolve-Path .\dbt).Path


Después verificar:

powershell
dbt debug --project-dir dbt


El resultado esperado es:


All checks passed!


---

## 4. Levantar infraestructura

Abrir Docker Desktop.

Después ejecutar:

powershell
docker compose up -d


Verificar:

powershell
docker compose ps


Los servicios principales deben mostrar:


PostgreSQL → activo y saludable
Kafka      → activo


---

## 5. Verificar conexión a PostgreSQL

Ejecutar:

powershell
Test-NetConnection localhost -Port 5433


Resultado esperado:


TcpTestSucceeded : True


---

## 6. Ejecutar el pipeline orquestado

Ejecutar:

powershell
python orchestration\flujo_fase1.py


El flujo coordina las principales etapas del pipeline:


Infraestructura
↓
Batch
↓
Streaming Transmetro
↓
Streaming Transurbano
↓
Streaming Aerómetro
↓
CDC
↓
Staging
↓
dbt run
↓
dbt test
↓
Métricas


Al finalizar debe indicar que el pipeline terminó correctamente.

---

## 7. Ejecutar dbt manualmente

Si se desea ejecutar únicamente las transformaciones:

powershell
dbt run --project-dir dbt


Para ejecutar todas las pruebas:

powershell
dbt test --project-dir dbt


Al cierre del bloque de gobernanza de la Fase 3 se ejecutaron:


91 pruebas
91 PASS
0 WARN
0 ERROR


---

## 8. Validar Gold

Verificar la tabla principal de abordajes:

powershell
docker exec -it redmetro-postgres psql -U red_user -d red_metropolitana -c "SELECT COUNT(*) FROM gold.fact_abordajes;"


Resultado de referencia:


1688959


Verificar viajes MetroRiel:

powershell
docker exec -it redmetro-postgres psql -U red_user -d red_metropolitana -c "SELECT COUNT(*) FROM gold.fact_viajes_metroriel;"


Resultado de referencia:


295511


---

## 9. Validar Features

Ejecutar:

powershell
docker exec -it redmetro-postgres psql -U red_user -d red_metropolitana -c "SELECT COUNT(*) AS filas, COUNT(DISTINCT usuario_id) AS usuarios FROM features.features_usuario;"


Resultado de referencia:


filas     = 70380
usuarios  = 70380


Esto confirma el grano de una fila por usuario.

---

## 10. Abrir Tableau

Abrir el workbook:


tableau/Red_Metropolitana_Fase2.twb


La conexión utiliza:


Servidor: localhost
Puerto: 5433
Base de datos: red_metropolitana


Tableau debe consumir las vistas:


gold.vw_abordajes_analitica
gold.vw_cobertura_zonas
gold.vw_usuarios_multimodales
gold.vw_metroriel_demanda


---

## 11. Regenerar documentación y linaje dbt

Generar:

powershell
dbt docs generate --project-dir dbt


Levantar servidor:

powershell
dbt docs serve --project-dir dbt --port 8081


La documentación puede abrirse localmente en:


http://localhost:8081


Desde esta interfaz se puede revisar el grafo de linaje entre fuentes,
Staging, Silver y Gold.

---

## 12. Validar calidad

Ejecutar:

powershell
Get-Content sql\queries\validacion_calidad_fase3.sql -Raw | docker exec -i redmetro-postgres psql -U red_user -d red_metropolitana


El total de registros de cuarentena de referencia es:


9710


---

## 13. Validar demanda oficial

Ejecutar:

powershell
docker exec -it redmetro-postgres psql -U red_user -d red_metropolitana -c "SELECT SUM(cantidad_abordajes) FROM gold.fact_abordajes;"


Resultado:


1688959


La misma cifra debe obtenerse desde:


gold.vw_abordajes_analitica


---

## 14. Finalizar sesión de trabajo

Para salir del entorno virtual:

powershell
deactivate


Para detener la infraestructura:

powershell
docker compose down


Los datos persistentes se conservan de acuerdo con los volúmenes definidos
en Docker Compose.

---

## Validaciones mínimas antes de considerar correcta una ejecución

Se considera que el proyecto se encuentra correctamente levantado cuando:

- PostgreSQL está saludable.
- Kafka está activo.
- `dbt debug` termina correctamente.
- el pipeline Prefect no presenta errores.
- los tests dbt terminan sin errores.
- Gold se encuentra disponible.
- Features se encuentra disponible.
- Tableau puede consultar las vistas Gold.
- los conteos principales corresponden con las métricas documentadas.