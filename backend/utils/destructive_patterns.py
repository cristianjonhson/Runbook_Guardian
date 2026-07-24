"""Patrones de acciones destructivas.

Lista determinista de comandos y operaciones peligrosas que el sistema
debe detectar y marcar con WARNING antes de presentar al usuario.
"""

import re

# Patrones individuales con descripción para mensajes de warning
DESTRUCTIVE_PATTERNS: list[tuple[str, str]] = [
    (r"rm\s+-rf", "Eliminación recursiva forzada (rm -rf)"),
    (r"rm\s+-f", "Eliminación forzada (rm -f)"),
    (r"drop\s+database", "Eliminación de base de datos (DROP DATABASE)"),
    (r"drop\s+table", "Eliminación de tabla (DROP TABLE)"),
    (r"delete\s+from", "Eliminación de registros (DELETE FROM)"),
    (r"\btruncate\b", "Truncado de tabla (TRUNCATE)"),
    (r"format\s+c:", "Formateo de disco (format C:)"),
    (r"shutdown\s+-h", "Apagado del sistema (shutdown)"),
    (r"\bhalt\b", "Detención del sistema (halt)"),
    (r"kill\s+-9", "Terminación forzada de proceso (kill -9)"),
    (r"iptables\s+-F", "Limpieza de reglas de firewall (iptables -F)"),
    (r"chmod\s+777", "Permisos abiertos a todos (chmod 777)"),
    (r"kubectl\s+delete", "Eliminación de recurso Kubernetes (kubectl delete)"),
    (r"terraform\s+destroy", "Destrucción de infraestructura (terraform destroy)"),
    (r"aws\s+.*--force", "Operación AWS forzada (--force)"),
]


def compile_patterns() -> list[tuple[re.Pattern, str]]:
    """Compila los patrones regex para uso eficiente.

    Returns:
        Lista de tuplas (patrón compilado, descripción).
    """
    return [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in DESTRUCTIVE_PATTERNS
    ]


# Patrones pre-compilados para reutilización
COMPILED_PATTERNS = compile_patterns()


def check_destructive(text: str) -> list[str]:
    """Verifica si un texto contiene acciones destructivas.

    Args:
        text: Texto a analizar (fragmento de runbook).

    Returns:
        Lista de descripciones de acciones destructivas encontradas.
        Lista vacía si el texto es seguro.
    """
    warnings: list[str] = []

    for pattern, description in COMPILED_PATTERNS:
        if pattern.search(text):
            warnings.append(description)

    return warnings
