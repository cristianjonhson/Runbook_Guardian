# Hackathon Rules — Runbook Guardian

## Duración disponible

- Tiempo de desarrollo limitado (hackathon).
- Priorizar MVP funcional sobre código perfecto.
- Cada decisión técnica debe evaluarse por: "¿esto me acerca a una demo funcional?"

## Criterios del jurado (esperados)

1. Innovación y originalidad de la solución.
2. Impacto real en el problema planteado.
3. Calidad técnica y arquitectura.
4. Demostración funcional en vivo.
5. Uso efectivo de las tecnologías requeridas (AWS, IA).
6. Claridad de presentación.
7. Viabilidad de producción.

## Tecnologías obligatorias

- Amazon Web Services (S3, Bedrock — al menos demostrar integración o plan).
- Inteligencia Artificial / Machine Learning (embeddings + RAG).
- Python como lenguaje principal.

## Restricciones del proyecto

1. La aplicación NO puede ejecutar comandos.
2. La aplicación NO puede modificar infraestructura.
3. La aplicación NO puede aprobar acciones sin intervención humana.
4. La aplicación NO puede responder sin evidencia documental.
5. El sistema debe funcionar offline como fallback.

## Condiciones de entrega

- Repositorio público en GitHub con README completo.
- Código fuente funcional y ejecutable.
- Documentación de arquitectura.
- Instrucciones de ejecución local.
- Video de demostración (si aplica).

## Duración de la demostración

- Máximo 5 minutos.
- Flujo recomendado para la demo:
  1. (0:00-0:30) Contexto del problema.
  2. (0:30-1:00) Solución propuesta.
  3. (1:00-3:30) Demo en vivo:
     - Consulta exitosa con evidencia.
     - Rechazo de runbook obsoleto.
     - Bloqueo de acción destructiva.
     - Funcionamiento offline.
  4. (3:30-4:30) Arquitectura y tecnologías.
  5. (4:30-5:00) Siguientes pasos y cierre.

## Requisitos del video (si aplica)

- Resolución mínima: 720p.
- Audio claro.
- Mostrar código ejecutándose, no solo slides.
- Incluir URL del repositorio.

## Reglas de propiedad intelectual

- El código producido durante la hackathon es propiedad del equipo.
- Se puede usar código open source con licencia compatible.
- Declarar dependencias y sus licencias en el README.

## Elementos necesarios para considerar el proyecto entregable

| # | Elemento | Estado requerido |
|---|----------|-----------------|
| 1 | Backend funcional (FastAPI) | Responde queries con evidencia |
| 2 | Frontend funcional (Streamlit) | Permite consultar y ver resultados |
| 3 | Al menos 5 runbooks sintéticos | Indexados y consultables |
| 4 | Validación de vigencia | Rechaza docs obsoletas |
| 5 | Detección de acciones destructivas | Bloquea con warning |
| 6 | Modo offline | Funciona sin AWS |
| 7 | README completo | Instrucciones claras |
| 8 | Demo ensayada | < 5 minutos |
| 9 | Tests básicos | Al menos unit tests de servicios críticos |
| 10 | Repositorio limpio | Sin secretos, con .gitignore correcto |

## Fallback para la demo

Si algún componente falla durante la presentación:

- Si ChromaDB falla → Respuestas precomputadas hardcodeadas para queries de demo.
- Si embeddings fallan → Búsqueda por keyword matching (fallback determinista).
- Si el frontend falla → Demo directa contra API con curl/httpie.
- Si todo falla → Video pregrabado como último recurso.

Siempre tener un `scripts/demo_queries.py` con queries que funcionan garantizadamente.
