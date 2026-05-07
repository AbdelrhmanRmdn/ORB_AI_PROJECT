from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class UserRecord:
    id: str | None
    name: str
    authorized: bool = True
    face_image_path: str | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UserRecord":
        return cls(
            id=_as_optional_str(row.get("id")),
            name=str(row.get("name", "")).strip(),
            authorized=bool(row.get("authorized", False)),
            face_image_path=_as_optional_str(row.get("face_image_path")),
            created_at=_as_optional_str(row.get("created_at")),
        )

    def to_insert_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "authorized": self.authorized,
            "face_image_path": self.face_image_path,
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class InteractionLog:
    user_id: str | None
    command: str
    ai_response: str
    timestamp: str = ""

    def to_insert_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "user_id": self.user_id,
            "command": self.command,
            "ai_response": self.ai_response,
            "timestamp": self.timestamp or utc_now_iso(),
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class SystemEvent:
    event_type: str
    message: str
    timestamp: str = ""

    def to_insert_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "message": self.message,
            "timestamp": self.timestamp or utc_now_iso(),
        }


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
