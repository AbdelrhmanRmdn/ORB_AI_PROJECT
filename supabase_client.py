from __future__ import annotations

from database.supabase_client import (
    SupabaseConfig,
    create_supabase_client,
    load_supabase_config,
)


def get_supabase_client():
    return create_supabase_client()


__all__ = [
    "SupabaseConfig",
    "create_supabase_client",
    "get_supabase_client",
    "load_supabase_config",
]
