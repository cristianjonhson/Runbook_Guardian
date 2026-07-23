"""Inyección de dependencias para la API.

Centraliza la creación de servicios para facilitar testing (mock) y
mantener los routers libres de lógica de inicialización.
"""

from backend.config import settings


def get_settings():
    """Retorna la instancia de configuración."""
    return settings
