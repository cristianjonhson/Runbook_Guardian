# Product Context — Runbook Guardian

## Problema

Durante un incidente, los operadores on-call buscan documentación bajo presión. Frecuentemente encuentran runbooks desactualizados, incompletos o sin contexto de versión, lo que incrementa el riesgo de ejecutar acciones incorrectas, destructivas o no auditables.

## Usuario objetivo

- Ingenieros on-call que responden a alertas fuera de horario.
- DevOps y SRE que necesitan pasos precisos durante mitigación.
- Equipos de plataforma que mantienen y auditan runbooks.

## Propuesta de valor

Un agente que responde SOLO con evidencia textual extraída de runbooks versionados, rechaza documentación obsoleta, y bloquea la sugerencia de acciones destructivas. El operador toma la decisión final; el sistema nunca ejecuta.

## Funcionalidades del MVP

1. Ingesta de runbooks Markdown con metadatos YAML (título, servicio, versión, fecha, estado).
2. Búsqueda semántica por similitud usando embeddings locales.
3. Validación de vigencia: rechazar docs con estado `deprecated` o sin revisión en > 90 días.
4. Respuesta con evidencia visible: fragmento textual, archivo fuente, versión, línea.
5. Detección y bloqueo de acciones destructivas en las sugerencias.
6. Interfaz web (Streamlit) para consultar el agente.
7. Modo offline completo sin dependencias cloud.
8. Fallback con respuestas precomputadas ante fallo del sistema de retrieval.

## Flujo principal

```
1. Operador describe síntoma o pregunta en lenguaje natural.
2. Sistema genera embedding de la consulta.
3. Sistema busca en ChromaDB los fragmentos más similares.
4. Sistema valida vigencia de cada runbook candidato.
5. Sistema filtra acciones destructivas de la respuesta.
6. Sistema presenta respuesta con:
   - Fragmento textual relevante.
   - Nombre del runbook fuente.
   - Versión y fecha de última revisión.
   - Líneas exactas del documento.
7. Operador decide si ejecutar los pasos sugeridos.
```

## Métricas de éxito

| Métrica | Objetivo |
|---------|----------|
| Respuesta con evidencia visible | 100% de las respuestas |
| Rechazo de docs obsoletas | 100% de docs con estado deprecated |
| Bloqueo de acciones destructivas | 100% de patrones conocidos |
| Tiempo de respuesta | < 3 segundos |
| Funcionamiento offline | Sin degradación funcional |
| Duración de demo | < 5 minutos |

## Funcionalidades fuera de alcance (MVP)

- Ejecución de comandos por parte del sistema.
- Modificación de infraestructura.
- Aprobación automática de acciones.
- Autenticación/autorización de usuarios.
- Integración con PagerDuty, Slack u otros.
- Despliegue en AWS (se prepara pero no es requisito para demo).
- Edición de runbooks desde la interfaz.
