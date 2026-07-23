# MCP Configuration — Runbook Guardian

## Ubicación

El archivo de configuración MCP debe estar en:
```
.kiro/settings/mcp.json
```

## Configuración recomendada

Copiar el siguiente contenido en `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-github@latest"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "disabled": true
    }
  }
}
```

## Servidores MCP

### 1. AWS Documentation (`aws-docs`)

| Campo | Valor |
|-------|-------|
| **Propósito** | Consultar documentación oficial de AWS (S3, Bedrock, CloudFormation) |
| **Herramientas expuestas** | `search_documentation`, `read_documentation` |
| **Permisos requeridos** | Ninguno (solo lectura de docs públicas) |
| **Riesgos** | Ninguno (read-only, sin acceso a cuenta AWS) |
| **Estado** | Habilitado (`disabled: false`) |

### 2. GitHub (`github`)

| Campo | Valor |
|-------|-------|
| **Propósito** | Consultar issues, PRs y documentación del repositorio |
| **Herramientas expuestas** | `search_repos`, `get_issue`, `list_issues`, `get_pr` |
| **Permisos requeridos** | `GITHUB_TOKEN` con scope `repo` (read) |
| **Riesgos** | Token con permisos amplios podría permitir escritura |
| **Estado** | Deshabilitado por defecto (`disabled: true`) |

## Prerequisitos

### Instalar uvx

```bash
# Con pip
pip install uv

# Con Homebrew (macOS)
brew install uv
```

Verificar instalación:
```bash
uvx --version
```

### Configurar GitHub Token (solo si habilitas github MCP)

```bash
# En tu .env o .zshrc
export GITHUB_TOKEN="ghp_tu_token_aqui"
```

**NUNCA** poner el token real en el archivo mcp.json. La sintaxis `${GITHUB_TOKEN}` referencia la variable de entorno.

## Validación

### Verificar AWS Docs MCP

1. Abrir Command Palette en Kiro (Cmd+Shift+P).
2. Buscar "MCP: List Servers" o revisar el panel MCP.
3. El servidor `aws-docs` debe aparecer como "Connected".
4. Probar buscando: "Amazon S3 versioning enable bucket".

### Verificar GitHub MCP (cuando se habilite)

1. Setear `GITHUB_TOKEN` en el entorno.
2. Cambiar `"disabled": true` a `"disabled": false` en mcp.json.
3. Verificar conexión en el panel MCP de Kiro.
4. Probar: buscar issues del repositorio.

## Herramientas que NO deben habilitarse

Por seguridad del proyecto, NO configurar MCPs que permitan:

- Eliminar repositorios o ramas.
- Hacer push o force push.
- Fusionar Pull Requests automáticamente.
- Eliminar o modificar infraestructura.
- Acceder a secretos de producción.
- Ejecutar comandos destructivos.

## Desactivar temporalmente

Para desactivar un MCP sin eliminarlo, cambiar:
```json
"disabled": true
```

Los servidores se reconectan automáticamente al guardar cambios en mcp.json.
