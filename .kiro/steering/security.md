# Security — Runbook Guardian

## Principio fundamental

El sistema es de SOLO LECTURA. No ejecuta, no modifica, no aprueba. El operador humano siempre toma la decisión final.

## Gestión de secretos

- Los secretos se almacenan EXCLUSIVAMENTE en variables de entorno (archivo `.env`).
- El archivo `.env` está en `.gitignore` y NUNCA se commitea.
- Se proporciona `.env.example` con claves sin valores reales.
- En CI/CD se usan GitHub Secrets.
- No se hardcodean tokens, API keys, contraseñas ni rutas privadas en el código.

## Variables de entorno

- Acceso centralizado a través de `backend/config.py` usando pydantic-settings.
- Validación de tipos al iniciar la aplicación.
- Valores por defecto solo para configuración no sensible.
- Variables sensibles (AWS keys, tokens) no tienen valor por defecto y fallan rápido si no están definidas.

## Validación de entradas

- Toda entrada del usuario se valida con Pydantic schemas antes de procesarse.
- Longitud máxima de query: 500 caracteres.
- No se permite inyección de paths (../, ~/, etc.) en nombres de runbook.
- Se sanitiza la entrada antes de usarla en búsquedas.

## Detección de acciones destructivas

El `SafetyService` mantiene una lista determinista de patrones peligrosos:

```
rm -rf, rm -f, drop database, drop table, delete from, truncate,
format, shutdown, halt, kill -9, iptables -F, chmod 777,
kubectl delete, terraform destroy, aws ... --force
```

- Si un fragmento de runbook contiene estos patrones, se marca con WARNING.
- El sistema NUNCA sugiere ejecutar estos comandos sin advertencia explícita.
- La lista de patrones es configurable via variable de entorno.

## Autorización

- MVP sin autenticación (acceso local únicamente).
- El sistema NO tiene permisos de escritura sobre ningún recurso externo.
- No hay roles ni permisos de usuario en el MVP.
- Fase 2: considerar API key simple para acceso al backend.

## Registro seguro (logging)

- Se usa structlog con formato JSON.
- NUNCA se loguean: contenidos completos de queries de usuario, paths absolutos del sistema, variables de entorno, tokens.
- Se loguean: timestamps, IDs de request, runbooks consultados, decisiones de seguridad (bloqueo/aprobación).

## Protección de información sensible

- Los runbooks pueden contener IPs, hostnames o rutas internas. El sistema los trata como texto plano para retrieval pero NO los expone en logs.
- No se almacenan consultas del usuario de forma persistente en el MVP.
- ChromaDB es local y no expone puerto de red.

## Principio de mínimo privilegio

- El proceso de backend solo necesita: lectura de `data/runbooks/`, lectura/escritura de `chroma_data/`.
- El frontend solo necesita: conexión HTTP al backend.
- Los scripts solo necesitan: lectura de `data/runbooks/`, escritura en `chroma_data/`.
- No se requieren permisos de root, acceso a red externa, ni escritura fuera del proyecto.

## MCP y herramientas externas

- Los servidores MCP configurados son de SOLO LECTURA (documentación).
- No se habilitan herramientas MCP que puedan: eliminar repos, hacer push, modificar infraestructura, acceder a secretos.
- Los tokens de MCP se pasan por variable de entorno, nunca en archivos versionados.
