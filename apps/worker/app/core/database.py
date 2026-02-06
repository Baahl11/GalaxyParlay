"""
Database Core Module
Cliente de Supabase singleton.
"""

from supabase import Client, create_client

from app.config import settings

_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Obtener instancia singleton del cliente Supabase."""
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    return _supabase_client
