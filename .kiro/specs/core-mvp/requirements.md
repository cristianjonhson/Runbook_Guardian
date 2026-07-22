# Requirements — Core MVP (Runbook Guardian)

## Historias de usuario

### HU-001: Consultar runbook durante un incidente
**Como** ingeniero on-call,
**quiero** hacer una pregunta en lenguaje natural sobre un incidente,
**para** obtener los pasos correctos de mitigación respaldados por documentación versionada.

### HU-002: Ver evidencia de la respuesta
**Como** operador SRE,
**quiero** ver exactamente qué runbook, versión y líneas respaldan la respuesta,
**para** auditar que la información es confiable y actual.

### HU-003: Protección contra documentación obsoleta
**Como** líder de plataforma,
**quiero** que el sistema rechace runbooks desactualizados,
**para** evitar que los operadores sigan procedimientos que ya no aplican.

### HU-004: Protección contra acciones destructivas
**Como** ingeniero on-call bajo presión,
**quiero** que el sistema me advierta si un paso implica una acción destructiva,
**para** evitar ejecutar comandos irreversibles por error.

### HU-005: Funcionamiento offline
**Como** operador en una red restringida,
**quiero** que el sistema funcione sin conexión a servicios cloud,
**para** tener acceso a la documentación incluso durante fallos de red.

---

## Requerimientos funcionales

### REQ-F-001: Ingesta de runbooks
WHEN un archivo Markdown con frontmatter YAML válido es colocado en `data/runbooks/`,
THE SYSTEM SHALL parsearlo y extraer: título, servicio, versión, fecha de última revisión, estado, y contenido.

**Campos obligatorios del frontmatter:**
```yaml
title: string (requerido)
service: string (requerido)
version: string (requerido, semver)
last_reviewed: date (requerido, formato YYYY-MM-DD)
status: enum [active, deprecated, draft] (requerido)
```

### REQ-F-002: Indexación en vector store
WHEN el script de ingesta se ejecuta,
THE SYSTEM SHALL generar embeddings de cada sección del runbook y almacenarlos en ChromaDB con metadata asociada (título, servicio, versión, estado, fecha).

### REQ-F-003: Búsqueda semántica
WHEN el usuario envía una consulta de texto (1-500 caracteres),
THE SYSTEM SHALL generar un embedding de la consulta y retornar los top-5 fragmentos más similares del vector store.

### REQ-F-004: Validación de vigencia
WHEN un fragmento candidato proviene de un runbook con estado `deprecated` O con `last_reviewed` mayor a 90 días,
THE SYSTEM SHALL excluirlo de la respuesta y registrar el rechazo.

### REQ-F-005: Detección de acciones destructivas
WHEN un fragmento de respuesta contiene patrones destructivos (rm -rf, drop database, delete from, truncate, kill -9, terraform destroy, kubectl delete, chmod 777, shutdown, format, iptables -F),
THE SYSTEM SHALL marcarlo con un WARNING visible y explicar el riesgo antes de presentarlo.

### REQ-F-006: Respuesta con evidencia
WHEN el sistema genera una respuesta,
THE SYSTEM SHALL incluir para cada fragmento:
- Texto exacto del runbook (sin modificar).
- Nombre del archivo fuente.
- Versión del runbook.
- Fecha de última revisión.
- Número de sección o línea aproximada.
- Score de similitud.

### REQ-F-007: Endpoint de consulta
WHEN se recibe un POST en `/api/v1/query` con body `{"query": "texto"}`,
THE SYSTEM SHALL retornar un JSON con la estructura:
```json
{
  "query": "texto original",
  "results": [...],
  "warnings": [...],
  "rejected_sources": [...],
  "metadata": {"response_time_ms": N, "total_candidates": N}
}
```

### REQ-F-008: Endpoint de salud
WHEN se recibe un GET en `/api/v1/health`,
THE SYSTEM SHALL retornar `{"status": "healthy", "runbooks_indexed": N, "version": "0.1.0"}`.

### REQ-F-009: Interfaz de usuario
WHEN el operador accede a la interfaz Streamlit,
THE SYSTEM SHALL mostrar:
- Campo de texto para la consulta.
- Botón de envío.
- Resultados con evidencia visible (fuente, versión, fragmento).
- Warnings destacados visualmente.
- Indicador de runbooks rechazados por obsolescencia.

### REQ-F-010: Fallback ante fallo
WHEN el sistema de retrieval falla (ChromaDB no disponible o embeddings fallan),
THE SYSTEM SHALL retornar respuestas precomputadas para queries conocidas y un mensaje indicando que está en modo fallback.

---

## Requerimientos no funcionales

### REQ-NF-001: Rendimiento
- Tiempo de respuesta para una query: < 3 segundos (p95).
- Tiempo de indexación de 5 runbooks: < 30 segundos.
- Startup del backend: < 10 segundos.

### REQ-NF-002: Disponibilidad offline
- El sistema debe funcionar al 100% sin conexión a internet.
- No hay dependencias de APIs externas en el path crítico.

### REQ-NF-003: Seguridad
- El sistema no ejecuta comandos del sistema operativo.
- El sistema no modifica archivos fuera de `chroma_data/`.
- No se almacenan credenciales en código.

### REQ-NF-004: Mantenibilidad
- Cobertura de tests >= 70%.
- Lint sin errores (ruff).
- Type hints en interfaces públicas.

### REQ-NF-005: Portabilidad
- Ejecutable en cualquier sistema con Python 3.11+.
- Sin dependencias de hardware específico.
- Docker compose para ejecución reproducible.

---

## Criterios de aceptación

| ID | Criterio | Prueba |
|----|----------|--------|
| AC-001 | Query válida retorna fragmentos con fuente y versión | Test de integración con query conocida |
| AC-002 | Runbook deprecated es excluido de resultados | Test unitario con runbook status=deprecated |
| AC-003 | Runbook sin revisión > 90 días es excluido | Test unitario con fecha antigua |
| AC-004 | Comando destructivo genera WARNING | Test unitario por cada patrón |
| AC-005 | Respuesta incluye score de similitud | Verificar campo en response |
| AC-006 | Query vacía retorna error 422 | Test con payload vacío |
| AC-007 | Query > 500 chars retorna error 422 | Test con string largo |
| AC-008 | Health endpoint retorna conteo de runbooks | Test de integración |
| AC-009 | Frontend muestra resultados con evidencia | Verificación manual |
| AC-010 | Sistema funciona sin red | Test en modo offline |
| AC-011 | Fallback retorna respuestas precomputadas | Test con ChromaDB deshabilitado |

---

## Escenarios

### Escenario normal: Consulta exitosa
1. Operador escribe: "El servicio nginx no responde, ¿qué hago?"
2. Sistema busca en runbooks indexados.
3. Encuentra `service-restart-nginx.md` (activo, revisado hace 15 días).
4. Retorna fragmento: "Paso 1: Verificar estado con systemctl status nginx..."
5. Incluye: fuente, versión 1.2.0, línea 12, score 0.89.

### Escenario de error: Documentación obsoleta
1. Operador pregunta sobre un servicio legacy.
2. Único runbook encontrado tiene `status: deprecated`.
3. Sistema retorna: 0 resultados, 1 rejected_source con motivo "deprecated".
4. Frontend muestra: "No se encontró documentación vigente para esta consulta."

### Escenario de error: Acción destructiva
1. Operador pregunta: "¿Cómo libero espacio en disco?"
2. Runbook encontrado incluye: "Ejecutar rm -rf /tmp/logs/*"
3. Sistema retorna el fragmento con WARNING: "Este paso contiene una acción potencialmente destructiva (rm -rf). Verificar manualmente antes de ejecutar."

### Escenario alternativo: Modo fallback
1. ChromaDB no está disponible (archivo corrupto o no indexado).
2. Sistema detecta fallo en retrieval.
3. Retorna respuesta precomputada para queries conocidas.
4. Incluye metadata: `"mode": "fallback"`.
