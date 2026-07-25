#!/usr/bin/env python3
"""Script de demo — ejecuta queries predefinidas para la presentación.

Demuestra los 4 escenarios principales:
1. Consulta exitosa con evidencia.
2. Rechazo de documentación obsoleta.
3. Detección de acciones destructivas.
4. Funcionamiento del sistema.

Uso:
    # Asegurarse de que el backend esté corriendo en localhost:8000
    python scripts/demo_queries.py
"""

import json
import sys
import time

import requests

BACKEND_URL = "http://localhost:8000"
API_URL = f"{BACKEND_URL}/api/v1"


def print_header(text: str):
    """Imprime un header formateado."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_section(text: str):
    """Imprime una sección."""
    print(f"\n--- {text} ---")


def query(text: str) -> dict:
    """Ejecuta una query contra el API."""
    response = requests.post(
        f"{API_URL}/query",
        json={"query": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def check_backend():
    """Verifica que el backend esté corriendo."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        data = r.json()
        print(f"  Status: {data['status']}")
        print(f"  Runbooks indexados: {data['runbooks_indexed']}")
        print(f"  Versión: {data['version']}")
        return data["runbooks_indexed"] > 0
    except requests.exceptions.ConnectionError:
        print("  ERROR: Backend no disponible")
        print(f"  Ejecuta: uvicorn backend.main:app --port 8000")
        return False


def demo_1_successful_query():
    """Demo 1: Consulta exitosa con evidencia."""
    print_header("DEMO 1: Consulta exitosa con evidencia")
    print("  Query: 'El servicio nginx no responde, ¿qué hago?'")
    print()

    result = query("El servicio nginx no responde, ¿qué hago?")

    print(f"  Resultados: {len(result['results'])}")
    print(f"  Modo: {result['metadata']['mode']}")
    print(f"  Tiempo: {result['metadata']['response_time_ms']}ms")

    if result["results"]:
        top = result["results"][0]
        print(f"\n  TOP RESULTADO:")
        print(f"  Fuente: {top['source_file']}")
        print(f"  Versión: {top['version']}")
        print(f"  Sección: {top['section']}")
        print(f"  Score: {top['similarity_score']:.3f}")
        print(f"  Revisado: {top['last_reviewed']}")
        print(f"\n  Fragmento:")
        for line in top["text"].split("\n")[:5]:
            print(f"    {line}")
        if len(top["text"].split("\n")) > 5:
            print(f"    ... ({len(top['text'].split(chr(10)))} líneas total)")

    return len(result["results"]) > 0


def demo_2_deprecated_rejection():
    """Demo 2: Rechazo de documentación obsoleta."""
    print_header("DEMO 2: Rechazo de documentación obsoleta")
    print("  Query: 'java memory leak OutOfMemoryError'")
    print()

    result = query("java memory leak OutOfMemoryError")

    print(f"  Resultados válidos: {len(result['results'])}")
    print(f"  Fuentes rechazadas: {len(result['rejected_sources'])}")

    if result["rejected_sources"]:
        print(f"\n  FUENTES RECHAZADAS:")
        for rej in result["rejected_sources"][:3]:
            print(f"    - {rej['source_file']}: {rej['reason']}")

    return len(result["rejected_sources"]) > 0 and len(result["results"]) == 0


def demo_3_destructive_warning():
    """Demo 3: Detección de acciones destructivas."""
    print_header("DEMO 3: Detección de acciones destructivas")
    print("  Query: 'how to free disk space on full server'")
    print()

    result = query("how to free disk space on full server")

    print(f"  Resultados: {len(result['results'])}")
    print(f"  Warnings globales: {len(result['warnings'])}")

    has_destructive = False
    for res in result["results"]:
        if res["warnings"]:
            has_destructive = True
            print(f"\n  ADVERTENCIA en {res['source_file']}:")
            for w in res["warnings"]:
                print(f"    ⚠️  {w}")

    if result["warnings"]:
        print(f"\n  WARNINGS GLOBALES:")
        for w in result["warnings"]:
            print(f"    ⚠️  {w}")

    return has_destructive


def demo_4_system_health():
    """Demo 4: Estado del sistema."""
    print_header("DEMO 4: Estado del sistema")

    # Health
    print_section("Health Check")
    r = requests.get(f"{API_URL}/health", timeout=5)
    health = r.json()
    print(f"  Status: {health['status']}")
    print(f"  Runbooks: {health['runbooks_indexed']}")

    # Runbooks list
    print_section("Runbooks disponibles")
    r = requests.get(f"{API_URL}/runbooks", timeout=5)
    runbooks = r.json()
    for rb in runbooks:
        status_icon = "✓" if rb["status"] == "active" else "✗"
        print(f"  {status_icon} {rb['title']} (v{rb['version']}, {rb['status']})")

    return True


def main():
    """Ejecuta todas las demos."""
    print_header("RUNBOOK GUARDIAN — Demo de presentación")
    print("  Agente seguro para equipos on-call")
    print("  Responde con evidencia de runbooks versionados")

    print_section("Verificando backend")
    if not check_backend():
        print("\n  Abortando demo. Inicia el backend primero.")
        sys.exit(1)

    results = []
    start = time.time()

    results.append(("Consulta exitosa", demo_1_successful_query()))
    results.append(("Rechazo obsoleta", demo_2_deprecated_rejection()))
    results.append(("Warning destructivo", demo_3_destructive_warning()))
    results.append(("Estado del sistema", demo_4_system_health()))

    elapsed = time.time() - start

    # Resumen
    print_header("RESUMEN DE DEMO")
    for name, passed in results:
        icon = "✓" if passed else "✗"
        print(f"  {icon} {name}")

    print(f"\n  Tiempo total: {elapsed:.1f}s")
    all_passed = all(r[1] for r in results)
    print(f"  Estado: {'LISTO PARA PRESENTAR' if all_passed else 'REQUIERE REVISIÓN'}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
