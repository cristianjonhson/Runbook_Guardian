# Tasks — Core MVP (Runbook Guardian)

## Resumen de implementación

Cada tarea es un incremento funcional verificable. Se implementan en orden.
Rama principal: `feature/core-mvp` (backend + lógica) y `feature/frontend` (UI).

---

## Tareas

- [ ] 1. Crear estructura base del backend con FastAPI
- [ ] 2. Implementar configuración centralizada (config.py)
- [ ] 3. Crear modelos de dominio (Runbook, Query)
- [ ] 4. Implementar markdown parser con extracción de YAML frontmatter
- [ ] 5. Crear runbooks sintéticos de ejemplo (5 mínimo)
- [ ] 6. Implementar RunbookRepository (lectura de filesystem)
- [ ] 7. Implementar VectorRepository (ChromaDB wrapper)
- [ ] 8. Implementar RetrievalService (embeddings + búsqueda)
- [ ] 9. Implementar ValidationService (vigencia de runbooks)
- [ ] 10. Implementar SafetyService (detección de acciones destructivas)
- [ ] 11. Implementar QueryService (orquestador)
- [ ] 12. Crear endpoint POST /api/v1/query
- [ ] 13. Crear endpoint GET /api/v1/health
- [ ] 14. Implementar sistema de fallback
- [ ] 15. Crear script de ingesta (ingest_runbooks.py)
- [ ] 16. Implementar interfaz Streamlit
- [ ] 17. Crear tests unitarios de servicios críticos
- [ ] 18. Crear tests de integración del flujo completo
- [ ] 19. Crear script de demo (demo_queries.py)
- [ ] 20. Validación final del MVP

---

## Detalle por tarea

### Tarea 1: Crear estructura base del backend con FastAPI

**Objetivo:** Tener un backend que arranca y responde en `/api/v1/health`.

**Archivos afectados:**
- `backend/main.py`
- `backend/api/__init__.py`
- `backend/api/router.py`
- `backend/api/schemas.py`
- `backend/api/dependencies.py`

**Dependencias:** Ninguna.

**Criterio de finalización:** `uvicorn backend.main:app` arranca sin error y `/docs` muestra Swagger UI.

**Pruebas requeridas:** Test manual de arranque.

**Rama:** `feature/core-mvp`

---

### Tarea 2: Implementar configuración centralizada

**Objetivo:** Centralizar todas las variables de entorno en un Settings object validado.

**Archivos afectados:**
- `backend/config.py`

**Dependencias:** Tarea 1.

**Criterio de finalización:** Import de `settings` funciona con `.env.example`.

**Pruebas requeridas:** Test unitario que valida carga de settings con defaults.

**Rama:** `feature/core-mvp`

---

### Tarea 3: Crear modelos de dominio

**Objetivo:** Definir las estructuras de datos del dominio.

**Archivos afectados:**
- `backend/models/__init__.py`
- `backend/models/runbook.py`
- `backend/models/query.py`

**Dependencias:** Tarea 2.

**Criterio de finalización:** Modelos importables, validación Pydantic funciona.

**Pruebas requeridas:** Test unitario de serialización/deserialización.

**Rama:** `feature/core-mvp`

---

### Tarea 4: Implementar markdown parser

**Objetivo:** Parsear archivos .md con YAML frontmatter y dividir en secciones.

**Archivos afectados:**
- `backend/utils/__init__.py`
- `backend/utils/markdown_parser.py`

**Dependencias:** Tarea 3.

**Criterio de finalización:** Parser retorna RunbookMetadata + lista de secciones con línea de inicio.

**Pruebas requeridas:** `tests/unit/test_markdown_parser.py` — archivos válidos, inválidos, sin frontmatter.

**Rama:** `feature/core-mvp`

---

### Tarea 5: Crear runbooks sintéticos de ejemplo

**Objetivo:** Tener al menos 5 runbooks realistas para testing y demo.

**Archivos afectados:**
- `data/runbooks/high-cpu-linux.md`
- `data/runbooks/disk-full-cleanup.md`
- `data/runbooks/service-restart-nginx.md`
- `data/runbooks/database-connection-pool.md`
- `data/runbooks/memory-leak-java.md`

**Dependencias:** Ninguna.

**Criterio de finalización:** Cada runbook tiene frontmatter válido, al menos 3 secciones (Symptoms, Diagnosis, Resolution), y contenido realista.

**Pruebas requeridas:** `scripts/validate_runbooks.py` pasa sin errores.

**Rama:** `feature/core-mvp`

---

### Tarea 6: Implementar RunbookRepository

**Objetivo:** Leer y parsear todos los runbooks del filesystem.

**Archivos afectados:**
- `backend/repositories/__init__.py`
- `backend/repositories/runbook_repository.py`

**Dependencias:** Tareas 4, 5.

**Criterio de finalización:** `list_all()` retorna 5 runbooks parseados, `get_by_service("nginx")` filtra correctamente.

**Pruebas requeridas:** Test unitario con fixtures en `tests/fixtures/`.

**Rama:** `feature/core-mvp`

---

### Tarea 7: Implementar VectorRepository

**Objetivo:** Wrapper sobre ChromaDB para indexar y buscar documentos.

**Archivos afectados:**
- `backend/repositories/vector_repository.py`

**Dependencias:** Tarea 2 (config para chroma_persist_dir).

**Criterio de finalización:** Puede indexar documentos con metadata y buscar por embedding retornando top-k con scores.

**Pruebas requeridas:** Test unitario con ChromaDB ephemeral client.

**Rama:** `feature/core-mvp`

---

### Tarea 8: Implementar RetrievalService

**Objetivo:** Generar embeddings y buscar fragmentos relevantes.

**Archivos afectados:**
- `backend/services/__init__.py`
- `backend/services/retrieval_service.py`

**Dependencias:** Tareas 7.

**Criterio de finalización:** `search("nginx not responding")` retorna candidatos del runbook de nginx con score > 0.5.

**Pruebas requeridas:** `tests/unit/test_retrieval_service.py` con mock de vector repo.

**Rama:** `feature/core-mvp`

---

### Tarea 9: Implementar ValidationService

**Objetivo:** Filtrar runbooks por vigencia.

**Archivos afectados:**
- `backend/services/validation_service.py`

**Dependencias:** Tarea 3 (modelos).

**Criterio de finalización:**
- Excluye runbooks con `status=deprecated`.
- Excluye runbooks con `last_reviewed` > 90 días.
- Retorna lista de válidos + rechazados con motivo.

**Pruebas requeridas:** `tests/unit/test_validation_service.py` — deprecated, stale, valid, missing fields.

**Rama:** `feature/core-mvp`

---

### Tarea 10: Implementar SafetyService

**Objetivo:** Detectar y marcar acciones destructivas en fragmentos.

**Archivos afectados:**
- `backend/services/safety_service.py`
- `backend/utils/destructive_patterns.py`

**Dependencias:** Tarea 2 (config para patterns).

**Criterio de finalización:** Detecta todos los patrones listados en security.md y marca fragmentos con WARNING.

**Pruebas requeridas:** `tests/unit/test_safety_service.py` — un test por cada patrón destructivo + test con texto seguro.

**Rama:** `feature/core-mvp`

---

### Tarea 11: Implementar QueryService

**Objetivo:** Orquestar el flujo completo de consulta.

**Archivos afectados:**
- `backend/services/query_service.py`

**Dependencias:** Tareas 8, 9, 10.

**Criterio de finalización:** `process_query("texto")` ejecuta retrieval → validación → seguridad → respuesta completa.

**Pruebas requeridas:** Test unitario con mocks de los tres servicios dependientes.

**Rama:** `feature/core-mvp`

---

### Tarea 12: Crear endpoint POST /api/v1/query

**Objetivo:** Exponer la consulta como API REST.

**Archivos afectados:**
- `backend/api/router.py`
- `backend/api/schemas.py`
- `backend/api/dependencies.py`

**Dependencias:** Tarea 11.

**Criterio de finalización:** POST con query válida retorna QueryResponse con evidence. POST con query inválida retorna 422.

**Pruebas requeridas:** `tests/integration/test_query_endpoint.py`

**Rama:** `feature/core-mvp`

---

### Tarea 13: Crear endpoint GET /api/v1/health

**Objetivo:** Endpoint de verificación con conteo de runbooks indexados.

**Archivos afectados:**
- `backend/api/router.py`
- `backend/api/schemas.py`

**Dependencias:** Tarea 7.

**Criterio de finalización:** Retorna status, conteo de documentos en ChromaDB, y versión de la app.

**Pruebas requeridas:** Test de integración.

**Rama:** `feature/core-mvp`

---

### Tarea 14: Implementar sistema de fallback

**Objetivo:** Respuestas precomputadas cuando el retrieval falla.

**Archivos afectados:**
- `backend/services/fallback_service.py`
- `backend/services/query_service.py` (integrar fallback)
- `data/fallback_responses.json`

**Dependencias:** Tarea 11.

**Criterio de finalización:** Si ChromaDB falla, el sistema retorna respuesta precomputada con `mode: "fallback"`.

**Pruebas requeridas:** Test unitario simulando fallo de ChromaDB.

**Rama:** `feature/core-mvp`

---

### Tarea 15: Crear script de ingesta

**Objetivo:** Script que indexa todos los runbooks en ChromaDB.

**Archivos afectados:**
- `scripts/ingest_runbooks.py`

**Dependencias:** Tareas 6, 7, 8.

**Criterio de finalización:** Ejecuta sin error, reporta N runbooks indexados, N secciones totales.

**Pruebas requeridas:** Ejecución exitosa con los 5 runbooks de ejemplo.

**Rama:** `feature/core-mvp`

---

### Tarea 16: Implementar interfaz Streamlit

**Objetivo:** UI para consultar el agente y ver resultados con evidencia.

**Archivos afectados:**
- `frontend/app.py`
- `frontend/components/` (si necesario)

**Dependencias:** Tarea 12.

**Criterio de finalización:** UI permite escribir query, ver resultados con fuente/versión, ver warnings en color, ver rechazados.

**Pruebas requeridas:** Verificación manual (Streamlit no se testea unitariamente en MVP).

**Rama:** `feature/frontend`

---

### Tarea 17: Crear tests unitarios de servicios críticos

**Objetivo:** Cobertura >= 70% en servicios de backend.

**Archivos afectados:**
- `tests/unit/test_validation_service.py`
- `tests/unit/test_safety_service.py`
- `tests/unit/test_markdown_parser.py`
- `tests/unit/test_retrieval_service.py`
- `tests/conftest.py`
- `tests/fixtures/` (runbooks de prueba)

**Dependencias:** Tareas 4, 8, 9, 10.

**Criterio de finalización:** `pytest tests/unit/ -v` pasa al 100%. Cobertura >= 70%.

**Pruebas requeridas:** Son las pruebas mismas.

**Rama:** `feature/core-mvp`

---

### Tarea 18: Crear tests de integración

**Objetivo:** Validar flujo completo end-to-end.

**Archivos afectados:**
- `tests/integration/test_query_endpoint.py`
- `tests/integration/test_query_flow.py`

**Dependencias:** Tareas 12, 15.

**Criterio de finalización:** Tests que hacen POST a `/api/v1/query` y validan estructura completa de respuesta.

**Pruebas requeridas:** Son las pruebas mismas.

**Rama:** `feature/core-mvp`

---

### Tarea 19: Crear script de demo

**Objetivo:** Script reproducible para ensayar la presentación.

**Archivos afectados:**
- `scripts/demo_queries.py`

**Dependencias:** Tarea 15 (runbooks indexados).

**Criterio de finalización:** Ejecuta 4 queries (exitosa, obsoleta, destructiva, fallback) y muestra resultados formateados.

**Pruebas requeridas:** Ejecución exitosa, output legible.

**Rama:** `feature/core-mvp`

---

### Tarea 20: Validación final del MVP

**Objetivo:** Confirmar que todos los criterios de aceptación se cumplen.

**Archivos afectados:** Ninguno (solo validación).

**Dependencias:** Todas las anteriores.

**Criterio de finalización:**
- [ ] `pytest` pasa al 100%.
- [ ] `ruff check` sin errores.
- [ ] Demo ejecuta en < 5 minutos.
- [ ] Funciona offline.
- [ ] No hay secretos en el código.
- [ ] README actualizado.

**Pruebas requeridas:** Checklist de validación completa.

**Rama:** `develop` (después de merge de features)
