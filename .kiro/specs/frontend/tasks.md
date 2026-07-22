# Tasks — Frontend (Runbook Guardian)

## Rama: `feature/frontend`

- [ ] 1. Crear aplicación Streamlit base con header y input
- [ ] 2. Implementar conexión con backend API
- [ ] 3. Renderizar resultados con evidencia (cards)
- [ ] 4. Agregar indicadores de warnings (acciones destructivas)
- [ ] 5. Agregar panel de fuentes rechazadas
- [ ] 6. Agregar banner de modo fallback
- [ ] 7. Agregar manejo de errores de conexión
- [ ] 8. Agregar metadata (tiempo de respuesta, candidatos)
- [ ] 9. Validación visual completa

---

## Detalle

### Tarea 1: App base con header e input

**Archivos:** `frontend/app.py`
**Criterio:** Streamlit arranca, muestra título y campo de texto.
**Dependencias:** Ninguna.

### Tarea 2: Conexión con backend

**Archivos:** `frontend/app.py`
**Criterio:** Query enviada al backend, respuesta recibida y parseada.
**Dependencias:** Backend en ejecución (tarea 12 de core-mvp).

### Tarea 3: Renderizar resultados

**Archivos:** `frontend/app.py`
**Criterio:** Cada resultado muestra texto, fuente, versión, fecha, score.
**Dependencias:** Tarea 2.

### Tarea 4: Warnings visuales

**Archivos:** `frontend/app.py`
**Criterio:** Resultados con warnings muestran borde rojo y texto de advertencia.
**Dependencias:** Tarea 3.

### Tarea 5: Panel de rechazados

**Archivos:** `frontend/app.py`
**Criterio:** Expander muestra runbooks rechazados con motivo.
**Dependencias:** Tarea 3.

### Tarea 6: Banner fallback

**Archivos:** `frontend/app.py`
**Criterio:** Si mode=fallback, banner amarillo visible arriba de resultados.
**Dependencias:** Tarea 2.

### Tarea 7: Manejo de errores

**Archivos:** `frontend/app.py`
**Criterio:** Si backend no responde, mensaje de error claro (no stack trace).
**Dependencias:** Tarea 2.

### Tarea 8: Metadata

**Archivos:** `frontend/app.py`
**Criterio:** Muestra tiempo de respuesta y total de candidatos al pie.
**Dependencias:** Tarea 3.

### Tarea 9: Validación visual

**Archivos:** Ninguno (solo validación).
**Criterio:** Demo completa funciona visualmente. Todos los estados verificados.
**Dependencias:** Todas las anteriores.
