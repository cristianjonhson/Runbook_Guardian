#!/usr/bin/env python3
"""Script de ingesta — indexa runbooks en ChromaDB.

Lee todos los archivos .md de data/runbooks/, extrae secciones,
genera embeddings con sentence-transformers, e indexa en ChromaDB.

Uso:
    python scripts/ingest_runbooks.py
    python scripts/ingest_runbooks.py --reset  # Limpia e reindexa
"""

import argparse
import sys
import time
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings
from backend.repositories.runbook_repository import RunbookRepository
from backend.repositories.vector_repository import VectorRepository
from backend.services.retrieval_service import RetrievalService


def main():
    """Ejecuta la ingesta de runbooks."""
    parser = argparse.ArgumentParser(description="Indexar runbooks en ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Eliminar índice existente antes de re-indexar",
    )
    parser.add_argument(
        "--runbooks-path",
        type=Path,
        default=settings.runbooks_path,
        help=f"Directorio de runbooks (default: {settings.runbooks_path})",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Runbook Guardian — Ingesta de Runbooks")
    print("=" * 60)
    print()

    start_time = time.time()

    # Inicializar componentes
    print("[1/4] Inicializando repositorios...")
    print(f"       Runbooks: {args.runbooks_path}")
    print(f"       ChromaDB: {settings.chroma_persist_dir}")
    print(f"       Modelo: {settings.embedding_model}")

    runbook_repo = RunbookRepository(runbooks_path=args.runbooks_path)
    vector_repo = VectorRepository(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )

    # Reset si se solicita
    if args.reset:
        print(f"\n[!] Eliminando índice existente ({vector_repo.count()} documentos)...")
        vector_repo.reset()
        print("    Índice limpio.")

    # Cargar runbooks
    print("\n[2/4] Cargando runbooks...")
    runbooks = runbook_repo.list_all()
    print(f"       {len(runbooks)} runbooks encontrados")

    if not runbooks:
        print("\n[ERROR] No se encontraron runbooks para indexar.")
        print(f"       Verifica que existan archivos .md en: {args.runbooks_path}")
        sys.exit(1)

    # Generar embeddings e indexar
    print("\n[3/4] Generando embeddings e indexando...")
    retrieval_service = RetrievalService(
        vector_repository=vector_repo,
        model_name=settings.embedding_model,
    )

    total_sections = 0
    errors = 0

    for runbook in runbooks:
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        embeddings: list[list[float]] = []

        for section in runbook.sections:
            if not section.content.strip():
                continue

            doc_id = (
                f"{runbook.metadata.file_path.replace('.md', '')}"
                f"__{section.heading.lower().replace(' ', '_')}"
            )

            metadata = {
                "title": runbook.metadata.title,
                "service": runbook.metadata.service,
                "version": runbook.metadata.version,
                "last_reviewed": str(runbook.metadata.last_reviewed),
                "status": runbook.metadata.status,
                "file_path": runbook.metadata.file_path,
                "section": section.heading,
                "line_start": section.line_start,
            }

            try:
                embedding = retrieval_service.generate_embedding(section.content)
                ids.append(doc_id)
                documents.append(section.content)
                metadatas.append(metadata)
                embeddings.append(embedding)
                total_sections += 1
            except Exception as e:
                print(f"       [WARN] Error en {doc_id}: {e}")
                errors += 1

        # Indexar batch por runbook
        if ids:
            vector_repo.index(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            print(f"       ✓ {runbook.metadata.file_path}: {len(ids)} secciones")

    # Resumen
    elapsed = time.time() - start_time
    print("\n[4/4] Ingesta completada")
    print(f"       {'─' * 40}")
    print(f"       Runbooks procesados:  {len(runbooks)}")
    print(f"       Secciones indexadas:  {total_sections}")
    print(f"       Errores:             {errors}")
    print(f"       Total en ChromaDB:   {vector_repo.count()}")
    print(f"       Tiempo:              {elapsed:.1f}s")
    print(f"       {'─' * 40}")
    print()

    if errors > 0:
        print(f"[WARN] Hubo {errors} errores durante la ingesta.")
        sys.exit(1)
    else:
        print("[OK] Ingesta exitosa. El sistema está listo para consultas.")


if __name__ == "__main__":
    main()
