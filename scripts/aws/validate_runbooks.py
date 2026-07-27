#!/usr/bin/env python3
"""Validar runbooks para compatibilidad con AWS.

Verifica que cada runbook tenga los metadatos mínimos requeridos
para carga en S3 y futura indexación en Bedrock Knowledge Base.

Uso:
    python scripts/aws/validate_runbooks.py
    python scripts/aws/validate_runbooks.py --path data/runbooks
"""

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path

import frontmatter

# Campos obligatorios para AWS
REQUIRED_FIELDS = {"title", "service", "version", "last_reviewed", "status"}
VALID_STATUSES = {"active", "deprecated", "draft", "archived"}


def compute_content_hash(content: str) -> str:
    """Calcula SHA-256 del contenido del runbook."""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"


def validate_runbook(file_path: Path, max_age_days: int = 90) -> list[str]:
    """Valida un runbook individual. Retorna lista de errores (vacía si válido)."""
    errors: list[str] = []

    try:
        raw = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
    except Exception as e:
        return [f"No se puede parsear: {e}"]

    metadata = dict(post.metadata)

    # Verificar campos obligatorios
    missing = REQUIRED_FIELDS - set(metadata.keys())
    if missing:
        errors.append(f"Campos faltantes: {sorted(missing)}")

    # Verificar status válido
    status = metadata.get("status", "")
    if status and status not in VALID_STATUSES:
        errors.append(f"Status inválido: '{status}' (permitidos: {sorted(VALID_STATUSES)})")

    # Verificar formato de versión (semver básico)
    version = metadata.get("version", "")
    if version and not all(p.isdigit() for p in version.split(".")):
        errors.append(f"Versión no es semver válida: '{version}'")

    # Verificar formato de fecha
    last_reviewed = metadata.get("last_reviewed")
    if last_reviewed:
        if isinstance(last_reviewed, str):
            try:
                last_reviewed = date.fromisoformat(last_reviewed)
            except ValueError:
                errors.append(f"Fecha inválida: '{last_reviewed}' (usar YYYY-MM-DD)")
                last_reviewed = None

        if isinstance(last_reviewed, date) and status == "active":
            age = (date.today() - last_reviewed).days
            if age > max_age_days:
                errors.append(
                    f"ADVERTENCIA: Runbook activo sin revisión hace {age} días (max: {max_age_days})"
                )

    # Verificar que tiene contenido
    if not post.content.strip():
        errors.append("Runbook sin contenido")

    # Verificar que tiene al menos una sección (##)
    if "## " not in post.content:
        errors.append("Runbook sin secciones (requiere al menos un ## header)")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validar runbooks para AWS")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data/runbooks"),
        help="Directorio de runbooks",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=90,
        help="Máximo de días sin revisión para runbooks activos",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"[ERROR] Directorio no encontrado: {args.path}")
        sys.exit(1)

    files = sorted(args.path.glob("*.md"))
    if not files:
        print(f"[ERROR] No se encontraron archivos .md en {args.path}")
        sys.exit(1)

    print("=" * 60)
    print("  Runbook Guardian — Validación para AWS")
    print("=" * 60)
    print(f"\n  Directorio: {args.path}")
    print(f"  Archivos:   {len(files)}")
    print(f"  Max age:    {args.max_age} días")
    print()

    total_errors = 0
    total_warnings = 0

    for f in files:
        errors = validate_runbook(f, max_age_days=args.max_age)
        warnings = [e for e in errors if e.startswith("ADVERTENCIA")]
        real_errors = [e for e in errors if not e.startswith("ADVERTENCIA")]

        if real_errors:
            print(f"  ✗ {f.name}")
            for err in real_errors:
                print(f"      ERROR: {err}")
            total_errors += len(real_errors)
        elif warnings:
            print(f"  ⚠ {f.name}")
            for w in warnings:
                print(f"      {w}")
            total_warnings += len(warnings)
        else:
            print(f"  ✓ {f.name}")

    print()
    print("-" * 60)
    print(f"  Total: {len(files)} runbooks, {total_errors} errores, {total_warnings} advertencias")

    if total_errors > 0:
        print("\n  [FAIL] Corregir errores antes de subir a S3.")
        sys.exit(1)
    else:
        print("\n  [OK] Todos los runbooks son válidos para AWS.")
        sys.exit(0)


if __name__ == "__main__":
    main()
