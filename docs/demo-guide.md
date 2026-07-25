# Demo Guide — Runbook Guardian

## Requisitos previos

- Python 3.11 instalado (`python3.11 --version`)
- Entorno virtual creado (`source .venv/bin/activate`)
- Dependencias instaladas (`pip install -r requirements.txt`)
- Runbooks indexados (`python scripts/ingest_runbooks.py`)

## Arranque rápido (2 terminales)

### Terminal 1: Backend
```bash
source .venv/bin/activate
uvicorn backend.main:app --port 8000
```

### Terminal 2: Frontend
```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

Abrir http://localhost:8501 en el navegador.

## Flujo de la demo (5 minutos)

### 1. Contexto del problema (0:00 - 0:30)

"Durante un incidente, los operadores buscan documentación bajo presión.
Frecuentemente encuentran runbooks desactualizados o sin contexto de versión."

### 2. Solución propuesta (0:30 - 1:00)

"Runbook Guardian es un agente RAG que responde SOLO con evidencia de runbooks
versionados. Rechaza documentación obsoleta y bloquea acciones destructivas."

### 3. Demo en vivo (1:00 - 3:30)

#### Escenario A: Consulta exitosa
**Query:** "El servicio nginx no responde, ¿qué hago?"
**Resultado esperado:** 5 fragmentos del runbook de nginx con fuente, versión y score.
**Punto clave:** "Cada respuesta incluye la fuente exacta para auditoría."

#### Escenario B: Documentación obsoleta
**Query:** "java memory leak OutOfMemoryError"
**Resultado esperado:** 0 resultados, panel de "Fuentes rechazadas" con razón "deprecated".
**Punto clave:** "El sistema protege contra documentación desactualizada."

#### Escenario C: Acción destructiva
**Query:** "how to free disk space on full server"
**Resultado esperado:** Resultados con WARNING rojo en la sección que contiene `rm -rf`.
**Punto clave:** "El operador ve la advertencia antes de ejecutar cualquier comando."

#### Escenario D: Modo fallback (opcional)
Detener ChromaDB o ejecutar con DB vacía.
**Resultado esperado:** Banner amarillo "Modo de respaldo activo", respuesta precomputada.
**Punto clave:** "El sistema funciona incluso si el retrieval falla."

### 4. Arquitectura (3:30 - 4:30)

Mostrar diagrama en docs o slides:
```
Streamlit → FastAPI → [Retrieval → Validation → Safety] → Response con evidencia
```

Tecnologías clave:
- Embeddings locales (all-MiniLM-L6-v2)
- ChromaDB como vector store
- Pipeline determinista de validación
- Fallback precomputado

### 5. Cierre (4:30 - 5:00)

- "El sistema nunca ejecuta comandos"
- "Funciona completamente offline"
- "Fase 2: Amazon S3 + Bedrock para mayor calidad"
- URL del repositorio

## Script de verificación

Antes de la demo, ejecutar:
```bash
source .venv/bin/activate
python scripts/demo_queries.py
```

Si las 4 demos pasan, el sistema está listo.

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Backend no arranca | Verificar que el puerto 8000 esté libre |
| 0 runbooks indexados | Ejecutar `python scripts/ingest_runbooks.py --reset` |
| Frontend no conecta | Verificar que el backend esté en puerto 8000 |
| Modelo no carga | Verificar conexión a internet para descarga inicial |
| Tests fallan | `pip install -r requirements.txt` con Python 3.11 |

## Plan de respaldo

Si algo falla durante la presentación:
1. Ejecutar `python scripts/demo_queries.py` y mostrar output en terminal.
2. Usar `curl` contra la API directamente.
3. Si todo falla, tener un video pregrabado.
