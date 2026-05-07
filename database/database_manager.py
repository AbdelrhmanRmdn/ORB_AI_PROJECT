from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import Settings, SETTINGS
from database.models import InteractionLog, SystemEvent, UserRecord
from database.queries import (
    INTERACTION_LOGS_TABLE,
    SYSTEM_EVENTS_TABLE,
    USER_COLUMNS,
    USERS_TABLE,
)
from database.supabase_client import create_supabase_client
from logging_config import get_logger


logger = get_logger("database.manager")


@dataclass(frozen=True)
class DatabaseHealth:
    enabled: bool
    configured: bool
    reachable: bool
    message: str


class DatabaseManager:
    """Thin repository layer for ORB data.

    The rest of the assistant talks to this class, not directly to Supabase.
    When Supabase is missing, offline, or disabled, methods return safe values.
    """

    def __init__(
        self,
        settings: Settings = SETTINGS,
        client: Any | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.settings = settings
        self.enabled = settings.database_enabled if enabled is None else enabled
        self._client = client
        self._client_loaded = client is not None

    @property
    def client(self) -> Any | None:
        if not self.enabled:
            return None
        if not self._client_loaded:
            self._client = create_supabase_client()
            self._client_loaded = True
        return self._client

    @property
    def available(self) -> bool:
        return self.client is not None

    def health_check(self) -> DatabaseHealth:
        if not self.enabled:
            return DatabaseHealth(False, False, False, "Database integration disabled")

        client = self.client
        if client is None:
            return DatabaseHealth(True, False, False, "Supabase is not configured")

        try:
            client.table(USERS_TABLE).select("id").limit(1).execute()
        except Exception as exc:
            logger.warning("Supabase health check failed: %s", exc)
            return DatabaseHealth(True, True, False, str(exc))

        return DatabaseHealth(True, True, True, "Supabase connection healthy")

    def get_authorized_users(self) -> list[UserRecord]:
        client = self.client
        if client is None or not self.settings.database_sync_users:
            return []

        try:
            response = (
                client.table(USERS_TABLE)
                .select(USER_COLUMNS)
                .eq("authorized", True)
                .execute()
            )
        except Exception as exc:
            logger.warning("Could not fetch authorized users from Supabase: %s", exc)
            return []

        rows = response.data or []
        return [UserRecord.from_row(row) for row in rows if row.get("name")]

    def get_users(self) -> list[UserRecord]:
        client = self.client
        if client is None:
            return []

        try:
            response = client.table(USERS_TABLE).select(USER_COLUMNS).execute()
        except Exception as exc:
            logger.warning("Could not fetch users from Supabase: %s", exc)
            return []

        rows = response.data or []
        return [UserRecord.from_row(row) for row in rows if row.get("name")]

    def get_user_by_name(self, name: str | None) -> UserRecord | None:
        if not name:
            return None
        client = self.client
        if client is None:
            return None

        try:
            response = (
                client.table(USERS_TABLE)
                .select(USER_COLUMNS)
                .ilike("name", name)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            logger.warning("Could not fetch Supabase user '%s': %s", name, exc)
            return None

        rows = response.data or []
        if not rows:
            return None
        return UserRecord.from_row(rows[0])

    def upsert_user(
        self,
        name: str,
        authorized: bool = True,
        face_image_path: str | None = None,
    ) -> UserRecord | None:
        client = self.client
        if client is None:
            return None

        record = UserRecord(
            id=None,
            name=name.strip().title(),
            authorized=authorized,
            face_image_path=face_image_path,
        )
        try:
            response = (
                client.table(USERS_TABLE)
                .upsert(record.to_insert_dict(), on_conflict="name")
                .execute()
            )
        except Exception as exc:
            logger.warning("Could not upsert Supabase user '%s': %s", name, exc)
            return None

        rows = response.data or []
        return UserRecord.from_row(rows[0]) if rows else record

    def set_user_authorized(self, name: str, authorized: bool) -> bool:
        updated = self.upsert_user(name=name, authorized=authorized)
        return updated is not None

    def sync_local_face_metadata(self, faces_dir: Path | None = None) -> int:
        client = self.client
        if client is None or not self.settings.database_sync_users:
            return 0

        root = faces_dir or self.settings.faces_dir
        if not root.exists():
            return 0

        synced = 0
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            name = path.parent.name if path.parent != root else path.stem
            record = UserRecord(
                id=None,
                name=name.replace("_", " ").strip().title(),
                authorized=True,
                face_image_path=str(path.relative_to(self.settings.project_root)),
            )
            try:
                (
                    client.table(USERS_TABLE)
                    .upsert(record.to_insert_dict(), on_conflict="name")
                    .execute()
                )
                synced += 1
            except Exception as exc:
                logger.warning("Could not sync face metadata for %s: %s", path, exc)
        return synced

    def log_interaction(
        self,
        user_name: str | None,
        command: str,
        ai_response: str,
    ) -> bool:
        if not self.settings.database_log_commands:
            return False
        client = self.client
        if client is None:
            return False

        user = self.get_user_by_name(user_name)
        payload = InteractionLog(
            user_id=user.id if user else None,
            command=command,
            ai_response=ai_response,
        ).to_insert_dict()

        try:
            client.table(INTERACTION_LOGS_TABLE).insert(payload).execute()
            return True
        except Exception as exc:
            logger.warning("Could not log interaction to Supabase: %s", exc)
            return False

    def log_event(self, event_type: str, message: str) -> bool:
        if not self.settings.database_log_events:
            return False
        client = self.client
        if client is None:
            return False

        try:
            client.table(SYSTEM_EVENTS_TABLE).insert(
                SystemEvent(event_type=event_type, message=message).to_insert_dict()
            ).execute()
            return True
        except Exception as exc:
            logger.warning("Could not log system event to Supabase: %s", exc)
            return False
