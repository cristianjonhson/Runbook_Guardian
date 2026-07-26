#!/usr/bin/env python3
"""Verificar estado de sincronización entre local y S3.

Compara runbooks locales contra los almacenados en S3 para detectar
diferencias en contenido, versiones o archivos faltantes.

Uso:
    python scripts/aws/sync_status.py --bucket <bucket-name>
    python scripts/aws/sync_status.py --bucket <bucket-name> --dry-run
"""

import argparse
import hashlib
import sys
from pathlib import Path

import frontmatter

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("[ERROR] boto3 no instalado. Ejecutar: pip install boto3")
    sys.exit(1)


def compute_sha256(content: str) -> str:
    """Calcula SHA-256 del contenido."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]


def get_local_runbooks(path: Path) -> dict[str, dict]:
    """Lee runbooks locales y retorna dict {filename: {hash, status, version}}."""
    runbooks = {}
    for f in sorted(path.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        metadata = dict(post.metadata)
        runbooks[f.name] = {
            "content_hash": compute_sha256(raw),
            "status": metadata.get("status", "unknown"),
            "version": metadata.get("version", "0.0.0"),
            "title": metadata.get("title", ""),
        }
    return runbooks


def get_s3_runbooks(s3_client, bucket: str, prefix: str = "runbooks/") -> dict[str, dict]:
    """Lista runbooks en S3 y retorna dict {filename: {hash, version_id}}."""
    runbooks = {}
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                filename = key.replace(prefix, "")
                if not filename.endswith(".md"):
                    continue

                # Obtener metadata del objeto
                try:
                    head = s3_client.head_object(Bucket=bucket, Key=key)
                    s3_metadata = head.get("Metadata", {})
                    runbooks[filename] = {
                        "content_hash": s3_metadata.get("content-hash", "unknown"),
                        "version_id": head.get("VersionId", "none"),
                        "last_modified": str(head.get("LastModified", "")),
                        "status": s3_metadata.get("runbook-status", "unknown"),
                    }
                except ClientError:
                    runbooks[filename] = {"content_hash": "error", "version_id": "error"}
    except ClientError as e:
        print(f"[ERROR] No se puede listar S3: {e}")
    return runbooks


def main():
    parser = argparse.ArgumentParser(description="Verificar sincronización local ↔ S3")
    parser.add_argument("--bucket", type=str, required=True, help="Nombre del bucket S3")
    parser.add_argument("--path", type=Path, default=Path("data/runbooks"), help="Directorio local")
    parser.add_argument("--prefix", type=str, default="runbooks/", help="Prefijo S3")
    parser.add_argument("--region", type=str, default="us-east-1", help="Región AWS")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar estado local (sin conectar a AWS)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Runbook Guardian — Estado de Sincronización")
    print("=" * 60)
    print(f"\n  Local:  {args.path}")
    print(f"  S3:     s3://{args.bucket}/{args.prefix}")
    print()

    # Leer runbooks locales
    local = get_local_runbooks(args.path)
    print(f"  Runbooks locales: {len(local)}")

    if args.dry_run:
        print("\n  [DRY-RUN] Mostrando solo estado local:")
        for name, info in local.items():
            print(f"    {name}: v{info['version']} ({info['status']}) hash={info['content_hash'][:8]}")
        sys.exit(0)

    # Leer runbooks en S3
    try:
        s3_client = boto3.client("s3", region_name=args.region)
        s3 = get_s3_runbooks(s3_client, args.bucket, args.prefix)
    except NoCredentialsError:
        print("[ERROR] No hay credenciales AWS. Usa --dry-run para modo offline.")
        sys.exit(1)

    print(f"  Runbooks en S3:   {len(s3)}")
    print()

    # Comparar
    only_local = set(local.keys()) - set(s3.keys())
    only_s3 = set(s3.keys()) - set(local.keys())
    common = set(local.keys()) & set(s3.keys())

    modified = []
    synced = []
    for name in sorted(common):
        if local[name]["content_hash"] != s3[name]["content_hash"]:
            modified.append(name)
        else:
            synced.append(name)

    # Reportar
    if synced:
        print("  ✓ Sincronizados:")
        for name in synced:
            print(f"      {name}")

    if modified:
        print("\n  ⚠ Modificados localmente (necesitan re-upload):")
        for name in modified:
            print(f"      {name} (local: {local[name]['content_hash'][:8]}... ≠ s3: {s3[name]['content_hash'][:8]}...)")

    if only_local:
        print("\n  + Solo en local (no subidos a S3):")
        for name in sorted(only_local):
            print(f"      {name}")

    if only_s3:
        print("\n  - Solo en S3 (no existe localmente):")
        for name in sorted(only_s3):
            print(f"      {name}")

    # Resumen
    print()
    print("-" * 60)
    print(f"  Sincronizados: {len(synced)}")
    print(f"  Modificados:   {len(modified)}")
    print(f"  Solo local:    {len(only_local)}")
    print(f"  Solo S3:       {len(only_s3)}")

    if modified or only_local:
        print("\n  [ACCIÓN] Ejecutar upload_runbooks.py para sincronizar.")
    else:
        print("\n  [OK] Todo sincronizado.")


if __name__ == "__main__":
    main()
