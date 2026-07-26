#!/usr/bin/env python3
"""Subir runbooks a Amazon S3 con metadata.

Sube archivos del directorio local a un bucket S3 versionado,
incluyendo metadata de trazabilidad en los headers del objeto.

Uso:
    python scripts/aws/upload_runbooks.py --bucket <bucket-name>
    python scripts/aws/upload_runbooks.py --bucket <bucket-name> --dry-run
"""

import argparse
import hashlib
import json
import sys
from datetime import date
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


def upload_runbook(
    s3_client,
    bucket: str,
    file_path: Path,
    s3_prefix: str = "runbooks/",
    dry_run: bool = False,
) -> dict | None:
    """Sube un runbook individual a S3 con metadata.

    Returns:
        Dict con información del upload (incluyendo VersionId) o None si falla.
    """
    raw = file_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    metadata = dict(post.metadata)

    s3_key = f"{s3_prefix}{file_path.name}"
    content_hash = compute_sha256(raw)

    # Metadata que se almacena en S3 object headers
    s3_metadata = {
        "runbook-title": str(metadata.get("title", ""))[:256],
        "runbook-service": str(metadata.get("service", ""))[:128],
        "runbook-version": str(metadata.get("version", ""))[:32],
        "runbook-status": str(metadata.get("status", ""))[:16],
        "runbook-last-reviewed": str(metadata.get("last_reviewed", "")),
        "content-hash": content_hash,
        "uploaded-at": str(date.today()),
    }

    if dry_run:
        return {
            "file": file_path.name,
            "s3_key": s3_key,
            "status": metadata.get("status"),
            "content_hash": content_hash,
            "version_id": "DRY-RUN",
            "action": "would_upload",
        }

    try:
        response = s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=raw.encode("utf-8"),
            ContentType="text/markdown",
            Metadata=s3_metadata,
        )
        return {
            "file": file_path.name,
            "s3_key": s3_key,
            "status": metadata.get("status"),
            "content_hash": content_hash,
            "version_id": response.get("VersionId", "none"),
            "action": "uploaded",
        }
    except ClientError as e:
        print(f"      [ERROR] {file_path.name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Subir runbooks a S3")
    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="Nombre del bucket S3 destino",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data/runbooks"),
        help="Directorio local de runbooks",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="runbooks/",
        help="Prefijo S3 (default: runbooks/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se haría sin ejecutar",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="Región AWS",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"[ERROR] Directorio no encontrado: {args.path}")
        sys.exit(1)

    files = sorted(args.path.glob("*.md"))
    if not files:
        print(f"[ERROR] No se encontraron runbooks en {args.path}")
        sys.exit(1)

    print("=" * 60)
    print("  Runbook Guardian — Upload de Runbooks a S3")
    print("=" * 60)
    print(f"\n  Bucket:   s3://{args.bucket}/{args.prefix}")
    print(f"  Source:   {args.path}")
    print(f"  Archivos: {len(files)}")
    print(f"  Región:   {args.region}")
    print(f"  Modo:     {'DRY-RUN (sin ejecutar)' if args.dry_run else 'REAL'}")
    print()

    # Inicializar cliente S3
    if not args.dry_run:
        try:
            s3_client = boto3.client("s3", region_name=args.region)
            # Verificar que el bucket existe
            s3_client.head_bucket(Bucket=args.bucket)
        except NoCredentialsError:
            print("[ERROR] No hay credenciales AWS configuradas.")
            sys.exit(1)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "404":
                print(f"[ERROR] Bucket '{args.bucket}' no existe.")
            elif code == "403":
                print(f"[ERROR] Sin permiso para acceder al bucket '{args.bucket}'.")
            else:
                print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        s3_client = None

    # Upload de cada runbook
    results = []
    for f in files:
        result = upload_runbook(
            s3_client=s3_client,
            bucket=args.bucket,
            file_path=f,
            s3_prefix=args.prefix,
            dry_run=args.dry_run,
        )
        if result:
            results.append(result)
            icon = "→" if args.dry_run else "✓"
            print(f"  {icon} {result['file']} → s3://{args.bucket}/{result['s3_key']} (v: {result['version_id'][:8]})")
        else:
            print(f"  ✗ {f.name}: error en upload")

    # Resumen
    print()
    print("-" * 60)
    uploaded = len([r for r in results if r])
    print(f"  {'Simulados' if args.dry_run else 'Subidos'}: {uploaded}/{len(files)}")

    if not args.dry_run and results:
        # Guardar registro de uploads
        upload_log = {
            "bucket": args.bucket,
            "prefix": args.prefix,
            "uploaded_at": str(date.today()),
            "files": results,
        }
        log_path = Path("data/manifests/last-upload.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(upload_log, indent=2), encoding="utf-8")
        print(f"  Log guardado: {log_path}")

    print()


if __name__ == "__main__":
    main()
