"""Patrones de acciones destructivas.

Lista determinista de comandos y operaciones peligrosas que el sistema
debe detectar y marcar con WARNING antes de presentar al usuario.
"""

import re

# Patrones individuales con descripción para mensajes de warning
DESTRUCTIVE_PATTERNS: list[tuple[str, str]] = [
    # --- Patrones de sistema operativo ---
    (r"rm\s+-rf", "Eliminación recursiva forzada (rm -rf)"),
    (r"rm\s+-f", "Eliminación forzada (rm -f)"),
    (r"format\s+c:", "Formateo de disco (format C:)"),
    (r"shutdown\s+-h", "Apagado del sistema (shutdown)"),
    (r"\bhalt\b", "Detención del sistema (halt)"),
    (r"kill\s+-9", "Terminación forzada de proceso (kill -9)"),
    (r"iptables\s+-F", "Limpieza de reglas de firewall (iptables -F)"),
    (r"chmod\s+777", "Permisos abiertos a todos (chmod 777)"),
    # --- Patrones de base de datos ---
    (r"drop\s+database", "Eliminación de base de datos (DROP DATABASE)"),
    (r"drop\s+table", "Eliminación de tabla (DROP TABLE)"),
    (r"delete\s+from", "Eliminación de registros (DELETE FROM)"),
    (r"\btruncate\b", "Truncado de tabla (TRUNCATE)"),
    # --- Patrones de infraestructura ---
    (r"kubectl\s+delete", "Eliminación de recurso Kubernetes (kubectl delete)"),
    (r"kubectl\s+delete\s+namespace", "Eliminación de namespace Kubernetes"),
    (r"terraform\s+destroy", "Destrucción de infraestructura (terraform destroy)"),
    # --- Patrones AWS ---
    (r"aws\s+.*--force", "Operación AWS forzada (--force)"),
    (r"aws\s+cloudformation\s+delete-stack", "Eliminación de stack CloudFormation"),
    (r"aws\s+s3\s+rb", "Eliminación de bucket S3 (aws s3 rb)"),
    (r"aws\s+s3\s+rm\s+.*--recursive", "Eliminación recursiva en S3"),
    (r"aws\s+iam\s+delete", "Eliminación de recurso IAM"),
    (r"aws\s+ec2\s+terminate", "Terminación de instancia EC2"),
    (r"aws\s+rds\s+delete", "Eliminación de base de datos RDS"),
    (r"aws\s+lambda\s+delete-function", "Eliminación de función Lambda"),
    # --- Patrones de Git destructivos ---
    (r"git\s+push\s+.*--force", "Force push a repositorio (git push --force)"),
    (r"git\s+reset\s+--hard", "Reset destructivo de Git"),
]

# Patrones que requieren aprobación humana explícita (risk_level: high)
APPROVAL_REQUIRED_PATTERNS: list[tuple[str, str]] = [
    (r"systemctl\s+restart.*prod", "Reinicio de servicio en producción"),
    (r"systemctl\s+stop", "Detención de servicio"),
    (r"kubectl\s+rollout\s+undo", "Rollback de despliegue Kubernetes"),
    (r"aws\s+cloudformation\s+execute-change-set", "Ejecución de Change Set"),
    (r"pg_terminate_backend", "Terminación de conexiones PostgreSQL"),
    (r"redis-cli\s+flushall", "Limpieza completa de Redis"),
    (r"ALTER\s+SYSTEM", "Modificación de configuración del sistema"),
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


def compile_approval_patterns() -> list[tuple[re.Pattern, str]]:
    """Compila los patrones de aprobación humana."""
    return [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in APPROVAL_REQUIRED_PATTERNS
    ]


# Patrones pre-compilados para reutilización
COMPILED_PATTERNS = compile_patterns()
COMPILED_APPROVAL_PATTERNS = compile_approval_patterns()


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


def check_approval_required(text: str) -> list[str]:
    """Verifica si un texto contiene acciones que requieren aprobación humana.

    Args:
        text: Texto a analizar.

    Returns:
        Lista de descripciones de acciones que requieren aprobación.
        Lista vacía si no se requiere aprobación.
    """
    approvals: list[str] = []

    for pattern, description in COMPILED_APPROVAL_PATTERNS:
        if pattern.search(text):
            approvals.append(description)

    return approvals
