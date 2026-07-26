#!/usr/bin/env python3
"""Genera manifiesto JSON de runbooks para trazabilidad AWS.

El manifiesto contiene metadata, hash de contenido y estado de cada runbook.
Se usa para validar citaciones de Bedrock contra fuentes autorizadas.

Uso:
    python scripts/aws/generate_manifest.py
    python scripts/aws/generate_manifest.py --output data/manifests/runbook-manifest.json
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import frontmatter


def compute_sha256(content: str) -> str:
    """Calcula SHA-256 del contenido."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_git_commit() -> str:
    """Obtiene el commit actual de git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def generate_runbook_entry(file_path: Path, s3_prefix: str = "runbooks/") -> dict | None:
    """Genera una entrada de manifiesto para un runbook."""
    try:
        raw = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
    except Exception:
        return None

    metadata = dict(post.metadata)
    status = metadata.get("status", "unknown")

    # Determinar S3 key basado en status
    s3_key = f"{s3_prefix}{file_path.name}"

    return {
        "runbook_id": f"RB-{file_path.stem.upper().replace('-', '_')}",
        "file_name": file_path.name,
        "title": metadata.get("title", ""),
        "service": metadata.get("service", ""),
        "semantic_version": metadata.get("version", "0.0.0"),
        "status": status,
        "last_reviewed": str(metadata.get("last_reviewed", "")),
        "valid_until": "",  # Se calcula: last_reviewed + 90 días
        "owner": metadata.get("owner", "platform-team"),
        "content_hash": f"sha256:{compute_sha256(raw)}",
        "git_commit": get_git_commit(),
        "s3_key": s3_key,
        "s3_version_id": "",  # Se llena después del upload
        "sections_count": post.content.count("## "),
        "generated_at": str(date.today()),
    }


def main():
    parser = argparse.ArgumentParser(description="Generar manifiesto de runbooks")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data/runbooks"),
        help="Directorio de runbooks",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/manifests/runbook-manifest.json"),
        help="Archivo de salida del manifiesto",
    )
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default="runbooks/",
        help="Prefijo S3 para las keys",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"[ERROR] Directorio no encontrado: {args.path}")
        sys.exit(1)

    files = sorted(args.path.glob("*.md"))

    print("=" * 60)
    print("  Runbook Guardian — Generación de Manifiesto")
    print("=" * 60)
    print(f"\n  Directorio: {args.path}")
    print(f"  Output:     {args.output}")
    print(f"  Runbooks:   {len(files)}")
    print()

    entries = []
    for f in files:
        entry = generate_runbook_entry(f, s3_prefix=args.s3_prefix)
        if entry:
            entries.append(entry)
            status_icon = "✓" if entry["status"] == "active" else "⚠"
            print(f"  {status_icon} {entry['runbook_id']}: {entry['title']} (v{entry['semantic_version']})")
        else:
            print(f"  ✗ {f.name}: error al parsear")

    # Construir manifiesto completo
    manifest = {
        "manifest_version": "1.0.0",
        "project": "runbook-guardian",
        "generated_at": str(date.today()),
        "git_commit": get_git_commit(),
        "total_runbooks": len(entries),
        "active_count": sum(1 for e in entries if e["status"] == "active"),
        "deprecated_count": sum(1 for e in entries if e["status"] == "deprecated"),
        "runbooks": entries,
    }

    # Escribir archivo
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("-" * 60)
    print(f"  Manifiesto generado: {args.output}")
    print(f"  Total: {manifest['total_runbooks']} ({manifest['active_count']} activos, {manifest['deprecated_count']} deprecated)")
    print()


if __name__ == "__main__":
    main()
