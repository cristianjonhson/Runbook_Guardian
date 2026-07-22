# Requirements — Frontend (Runbook Guardian)

## Historia de usuario

### HU-UI-001: Consultar el agente desde una interfaz visual
**Como** ingeniero on-call,
**quiero** escribir mi pregunta en una interfaz web simple,
**para** obtener respuestas sin necesidad de usar curl o herramientas CLI.

### HU-UI-002: Visualizar evidencia de la respuesta
**Como** operador SRE,
**quiero** ver claramente la fuente, versión y fragmento de cada resultado,
**para** confiar en que la información es actual y auditarla fácilmente.

### HU-UI-003: Identificar advertencias de seguridad
**Como** ingeniero on-call bajo presión,
**quiero** ver destacadas visualmente las acciones destructivas,
**para** no ejecutarlas accidentalmente.

---

## Requerimientos funcionales

### REQ-UI-001: Campo de consulta
WHEN el operador accede a la aplicación,
THE SYSTEM SHALL mostrar un campo de texto con placeholder "Describe el incidente o síntoma..." y un botón "Consultar".

### REQ-UI-002: Presentación de resultados
WHEN la API retorna resultados,
THE SYSTEM SHALL mostrar cada fragmento en una card con: texto del fragmento, nombre del archivo fuente, versión, fecha de revisión, sección, y score de similitud.

### REQ-UI-003: Indicador de warnings
WHEN un resultado contiene warnings de acciones destructivas,
THE SYSTEM SHALL mostrarlo con borde rojo/naranja y un ícono de advertencia, con el texto del warning visible.

### REQ-UI-004: Fuentes rechazadas
WHEN la API retorna rejected_sources,
THE SYSTEM SHALL mostrar un panel colapsable indicando qué runbooks fueron excluidos y por qué motivo.

### REQ-UI-005: Indicador de modo
WHEN la API retorna `metadata.mode = "fallback"`,
THE SYSTEM SHALL mostrar un banner amarillo indicando "Modo de respaldo activo — resultados pueden ser limitados".

### REQ-UI-006: Tiempo de respuesta
WHEN la API retorna metadata,
THE SYSTEM SHALL mostrar el tiempo de respuesta en milisegundos en la parte inferior de los resultados.

### REQ-UI-007: Estado vacío
WHEN no hay resultados ni rejected_sources,
THE SYSTEM SHALL mostrar "No se encontró documentación relevante para esta consulta. Intente reformular."

### REQ-UI-008: Error de conexión
WHEN la conexión al backend falla,
THE SYSTEM SHALL mostrar un mensaje de error claro con sugerencia de verificar que el backend está ejecutándose.

---

## Requerimientos no funcionales

- La interfaz debe cargar en < 3 segundos.
- No requiere autenticación.
- Responsive no es requisito (solo desktop para demo).
- No usa JavaScript custom.
- Colores accesibles (contraste WCAG AA mínimo para warnings).

---

## Criterios de aceptación

| ID | Criterio | Verificación |
|----|----------|-------------|
| AC-UI-001 | Input acepta texto de 1-500 caracteres | Prueba manual |
| AC-UI-002 | Resultados muestran fuente + versión + score | Inspección visual |
| AC-UI-003 | Warnings aparecen en rojo/naranja | Inspección visual |
| AC-UI-004 | Modo fallback muestra banner amarillo | Prueba con backend en fallback |
| AC-UI-005 | Error de conexión muestra mensaje útil | Prueba con backend apagado |
