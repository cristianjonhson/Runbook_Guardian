# Testing — Runbook Guardian

## Tipos de pruebas

| Tipo | Ubicación | Herramienta | Propósito |
|------|-----------|-------------|-----------|
| Unitarias | `tests/unit/` | pytest | Validar lógica de cada servicio aislado |
| Integración | `tests/integration/` | pytest + httpx | Validar flujo completo API → Service → Repository |
| Lint/Formato | CI + hook | ruff | Consistencia de código |
| Seguridad | hook | grep/regex | Detectar secretos o patrones peligrosos |

## Cobertura mínima

- Cobertura global: 70% (configurado en pyproject.toml).
- Servicios críticos (SafetyService, ValidationService): 90%.
- No se exige cobertura para: `__init__.py`, scripts de utilidad, frontend Streamlit.

## Herramientas

- `pytest` — Test runner principal.
- `pytest-asyncio` — Soporte para tests async.
- `pytest-cov` — Reporte de cobertura.
- `httpx` — AsyncClient para tests de integración FastAPI.
- `ruff` — Linter y formatter.

## Convenciones de nombres

- Archivos: `test_<nombre_modulo>.py`
- Funciones: `test_<accion>_<condicion>_<resultado_esperado>()`
- Ejemplos:
  - `test_validate_runbook_deprecated_returns_invalid()`
  - `test_safety_check_destructive_command_returns_warning()`
  - `test_query_valid_input_returns_evidence()`

## Datos de prueba

- Runbooks de test en `tests/fixtures/` (NO en `data/runbooks/`).
- Fixtures de pytest en `tests/conftest.py`.
- Cada test crea su propio estado; no depende de estado global.
- No se usa la base ChromaDB real en tests unitarios (mock).
- Tests de integración pueden usar ChromaDB en memoria (ephemeral client).

## Validaciones obligatorias antes de integrar una rama

| Validación | Comando | Criterio de éxito |
|-----------|---------|-------------------|
| Tests unitarios | `pytest tests/unit/ -v` | 0 fallos |
| Tests integración | `pytest tests/integration/ -v` | 0 fallos |
| Cobertura | `pytest --cov=backend --cov-fail-under=70` | >= 70% |
| Lint | `ruff check backend/ tests/` | 0 errores |
| Formato | `ruff format --check backend/ tests/` | Sin cambios pendientes |
| Seguridad | `grep -r "AWS_SECRET\|password\|token=" backend/` | Sin coincidencias |

## Reglas

1. No se marca una tarea como completada sin al menos un test que la valide.
2. Tests deben ser deterministas: no depender de hora, red, ni estado externo.
3. Tests deben ejecutarse en < 30 segundos (unitarios) y < 60 segundos (integración).
4. Cada bug fix debe acompañarse de un test que reproduce el bug.
5. Los tests de SafetyService deben cubrir TODOS los patrones destructivos listados en security.md.
