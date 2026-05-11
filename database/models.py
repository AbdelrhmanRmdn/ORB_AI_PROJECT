from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def face_label_from_name(name: str) -> str:
    label = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return label or "unknown_user"


@dataclass(frozen=True)
class UserRecord:
    """Internal user model mapped to the team's public.users table."""

    id: str | None
    name: str
    authorized: bool = True
    face_image_path: str | None = None
    created_at: str | None = None
    full_name: str | None = None
    display_name: str | None = None
    face_label: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UserRecord":
        full_name = _as_optional_str(row.get("full_name"))
        display_name = _as_optional_str(row.get("display_name"))
        legacy_name = _as_optional_str(row.get("name"))
        face_label = _as_optional_str(row.get("face_label"))
        name = display_name or full_name or legacy_name or face_label or ""
        authorized = row.get("is_authorized", row.get("authorized", False))
        face_path = row.get("face_embedding_path", row.get("face_image_path"))

        return cls(
            id=_as_optional_str(row.get("id")),
            name=name.strip(),
            authorized=bool(authorized),
            face_image_path=_as_optional_str(face_path),
            created_at=_as_optional_str(row.get("created_at")),
            full_name=full_name,
            display_name=display_name,
            face_label=face_label,
            updated_at=_as_optional_str(row.get("updated_at")),
        )

    def to_insert_dict(self) -> dict[str, Any]:
        display_name = self.display_name or self.name
        full_name = self.full_name or self.name
        face_label = self.face_label or face_label_from_name(self.name)
        payload: dict[str, Any] = {
            "full_name": full_name,
            "display_name": display_name,
            "is_authorized": self.authorized,
            "face_label": face_label,
            "face_embedding_path": self.face_image_path,
            "updated_at": utc_now_iso(),
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class InteractionLog:
    """Internal command log mapped to public.command_logs."""

    user_id: str | None
    command: str
    ai_response: str
    timestamp: str = ""
    detected_intent: str | None = None
    source: str = "voice"
    status: str = "success"

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "InteractionLog":
        return cls(
            user_id=_as_optional_str(row.get("user_id")),
            command=str(row.get("raw_command", row.get("command", ""))).strip(),
            ai_response=str(row.get("response_text", row.get("ai_response", ""))).strip(),
            timestamp=_as_optional_str(row.get("created_at", row.get("timestamp"))) or "",
            detected_intent=_as_optional_str(
                row.get("detected-intent", row.get("detected_intent"))
            ),
            source=_as_optional_str(row.get("source")) or "voice",
            status=_as_optional_str(row.get("status")) or "success",
        )

    def to_insert_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "user_id": self.user_id,
            "raw_command": self.command,
            "detected-intent": self.detected_intent,
            "response_text": self.ai_response,
            "source": self.source,
            "status": self.status,
        }
        if self.timestamp:
            payload["created_at"] = self.timestamp
        return _drop_none_except(payload, keep={"user_id"})


@dataclass(frozen=True)
class SystemEvent:
    event_type: str
    message: str
    timestamp: str = ""

    def to_insert_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "user_id": None,
            "raw_command": self.event_type,
            "detected-intent": self.event_type,
            "response_text": self.message,
            "source": "system",
            "status": "event",
        }
        if self.timestamp:
            payload["created_at"] = self.timestamp
        return payload


@dataclass(frozen=True)
class DeviceState:
    device_name: str
    current_user_id: str | None = None
    is_online: bool = True
    current_state: str | None = None
    last_command: str | None = None
    last_response: str | None = None
    updated_at: str = ""

    def to_insert_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "device_name": self.device_name,
            "current_user_id": self.current_user_id,
            "is_online": self.is_online,
            "current_state": self.current_state,
            "last_command": self.last_command,
            "last_response": self.last_response,
            "updated_at": self.updated_at or utc_now_iso(),
        }
        return {key: value for key, value in payload.items() if value is not None}


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _drop_none_except(
    payload: dict[str, Any],
    keep: set[str] | None = None,
) -> dict[str, Any]:
    keep = keep or set()
    return {
        key: value
        for key, value in payload.items()
        if value is not None or key in keep
    }
