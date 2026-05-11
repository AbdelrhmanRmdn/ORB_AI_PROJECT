from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from config import _load_env_file
from logging_config import get_logger


logger = get_logger("database.supabase_client")


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    key: str
    timeout_seconds: float = 5.0

    @property
    def configured(self) -> bool:
        return bool(self.url and self.key)


def load_supabase_config() -> SupabaseConfig:
    _load_env_file()
    try:
        timeout_seconds = float(os.getenv("SUPABASE_TIMEOUT_SECONDS", "5"))
    except ValueError:
        timeout_seconds = 5.0

    return SupabaseConfig(
        url=os.getenv("SUPABASE_URL", "").strip(),
        key=os.getenv("SUPABASE_KEY", "").strip(),
        timeout_seconds=timeout_seconds,
    )


def create_supabase_client(config: SupabaseConfig | None = None) -> Any | None:
    config = config or load_supabase_config()
    if not config.configured:
        logger.info("Supabase is not configured")
        return None

    try:
        import httpx
        from supabase import create_client
        from supabase.lib.client_options import SyncClientOptions
    except Exception as exc:
        logger.error("Supabase Python package is unavailable: %s", exc)
        return None

    try:
        http_client = httpx.Client(timeout=config.timeout_seconds)
        options = SyncClientOptions(httpx_client=http_client)
        return create_client(config.url, config.key, options=options)
    except Exception as exc:
        logger.error("Could not create Supabase client: %s", exc)
        return None
