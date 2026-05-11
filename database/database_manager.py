from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import Settings, SETTINGS
from database.models import (
    DeviceState,
    InteractionLog,
    SystemEvent,
    UserRecord,
    face_label_from_name,
)
from database.queries import (
    COMMAND_LOGS_TABLE,
    DEVICE_STATE_TABLE,
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
    This file is the only place that needs to know the team's table names.
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
                .eq("is_authorized", True)
                .execute()
            )
        except Exception as exc:
            logger.warning("Could not fetch authorized users from Supabase: %s", exc)
            return []

        rows = response.data or []
        return [UserRecord.from_row(row) for row in rows if _row_has_name(row)]

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
        return [UserRecord.from_row(row) for row in rows if _row_has_name(row)]

    def get_user_by_name(self, name: str | None) -> UserRecord | None:
        row = self._find_user_row(name)
        return UserRecord.from_row(row) if row else None

    def upsert_user(
        self,
        name: str,
        authorized: bool = True,
        face_image_path: str | None = None,
        full_name: str | None = None,
        display_name: str | None = None,
        face_label: str | None = None,
    ) -> UserRecord | None:
        client = self.client
        if client is None:
            return None

        cleaned_name = display_name.strip() if display_name else name.strip().title()
        if not cleaned_name:
            logger.warning("Could not upsert Supabase user without a name")
            return None

        record = UserRecord(
            id=None,
            name=cleaned_name,
            authorized=authorized,
            face_image_path=self._path_for_supabase(face_image_path),
            full_name=full_name.strip() if full_name else cleaned_name,
            display_name=cleaned_name,
            face_label=face_label or face_label_from_name(cleaned_name),
        )
        payload = record.to_insert_dict()

        try:
            existing = self._find_user_row(record.name, record.face_label)
            if existing and existing.get("id"):
                response = (
                    client.table(USERS_TABLE)
                    .update(payload)
                    .eq("id", existing["id"])
                    .execute()
                )
            else:
                response = client.table(USERS_TABLE).insert(payload).execute()
        except Exception as exc:
            logger.warning("Could not upsert Supabase user '%s': %s", name, exc)
            return None

        rows = response.data or []
        return UserRecord.from_row(rows[0]) if rows else record

    def save_user_face_data(
        self,
        display_name: str,
        face_image_path: str | Path,
        full_name: str | None = None,
        authorized: bool = True,
        face_label: str | None = None,
    ) -> UserRecord | None:
        """Save a user's face metadata into the team's public.users table.

        Call this when another part of the code captures or chooses a face image
        and needs to attach that image path to a Supabase user row.
        """
        return self.upsert_user(
            name=display_name,
            authorized=authorized,
            face_image_path=str(face_image_path),
            full_name=full_name,
            display_name=display_name,
            face_label=face_label,
        )

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
            record = self.upsert_user(
                name=name.replace("_", " ").strip().title(),
                authorized=True,
                face_image_path=self._path_for_supabase(path),
            )
            if record is not None:
                synced += 1
        return synced

    def log_interaction(
        self,
        user_name: str | None,
        command: str,
        ai_response: str,
        detected_intent: str | None = None,
        source: str = "voice",
        status: str = "success",
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
            detected_intent=detected_intent,
            source=source,
            status=status,
        ).to_insert_dict()

        inserted = False
        try:
            client.table(COMMAND_LOGS_TABLE).insert(payload).execute()
            inserted = True
        except Exception as exc:
            logger.warning("Could not log command to Supabase: %s", exc)

        self.update_device_state(
            current_user_id=user.id if user else None,
            current_state=detected_intent or status,
            last_command=command,
            last_response=ai_response,
            is_online=True,
        )
        return inserted

    def log_event(self, event_type: str, message: str) -> bool:
        if not self.settings.database_log_events:
            return False
        client = self.client
        if client is None:
            return False

        payload = SystemEvent(event_type=event_type, message=message).to_insert_dict()
        inserted = False
        try:
            client.table(COMMAND_LOGS_TABLE).insert(payload).execute()
            inserted = True
        except Exception as exc:
            logger.warning("Could not log system event to Supabase: %s", exc)

        self.update_device_state(
            current_state=event_type,
            last_command=event_type,
            last_response=message,
            is_online=event_type != "shutdown",
        )
        return inserted

    def update_device_state(
        self,
        current_user_id: str | None = None,
        current_state: str | None = None,
        last_command: str | None = None,
        last_response: str | None = None,
        is_online: bool = True,
    ) -> bool:
        client = self.client
        if client is None:
            return False

        payload = DeviceState(
            device_name=self.settings.device_name,
            current_user_id=current_user_id,
            is_online=is_online,
            current_state=current_state,
            last_command=last_command,
            last_response=last_response,
        ).to_insert_dict()

        try:
            existing_response = (
                client.table(DEVICE_STATE_TABLE)
                .select("id")
                .eq("device_name", self.settings.device_name)
                .limit(1)
                .execute()
            )
            rows = existing_response.data or []
            if rows and rows[0].get("id"):
                (
                    client.table(DEVICE_STATE_TABLE)
                    .update(payload)
                    .eq("id", rows[0]["id"])
                    .execute()
                )
            elif current_user_id is None:
                logger.info(
                    "Skipping device state insert because current_user_id is required"
                )
                return False
            else:
                client.table(DEVICE_STATE_TABLE).insert(payload).execute()
        except Exception as exc:
            logger.warning("Could not update Supabase device state: %s", exc)
            return False
        return True

    def _find_user_row(
        self,
        name: str | None,
        face_label: str | None = None,
    ) -> dict[str, Any] | None:
        client = self.client
        if client is None or not name:
            return None

        lookups = [
            ("display_name", name),
            ("full_name", name),
            ("face_label", face_label or face_label_from_name(name)),
        ]
        for column, value in lookups:
            if not value:
                continue
            try:
                response = (
                    client.table(USERS_TABLE)
                    .select(USER_COLUMNS)
                    .ilike(column, value)
                    .limit(1)
                    .execute()
                )
            except Exception as exc:
                logger.warning("Could not look up Supabase user '%s': %s", name, exc)
                return None

            rows = response.data or []
            if rows:
                return rows[0]
        return None

    def _path_for_supabase(self, path: str | Path | None) -> str | None:
        if path is None:
            return None

        text = str(path).strip()
        if not text:
            return None
        if "://" in text:
            return text

        path_obj = Path(text)
        try:
            if path_obj.is_absolute():
                return path_obj.resolve().relative_to(
                    self.settings.project_root
                ).as_posix()
        except ValueError:
            return path_obj.as_posix()

        return path_obj.as_posix()


def _row_has_name(row: dict[str, Any]) -> bool:
    return bool(
        row.get("display_name")
        or row.get("full_name")
        or row.get("name")
        or row.get("face_label")
    )


def save_user_face_data(
    display_name: str,
    face_image_path: str | Path,
    full_name: str | None = None,
    authorized: bool = True,
    face_label: str | None = None,
    database: DatabaseManager | None = None,
) -> UserRecord | None:
    """Convenience function for saving captured face data from anywhere."""
    manager = database or DatabaseManager()
    return manager.save_user_face_data(
        display_name=display_name,
        face_image_path=face_image_path,
        full_name=full_name,
        authorized=authorized,
        face_label=face_label,
    )
