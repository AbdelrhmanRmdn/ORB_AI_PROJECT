from dataclasses import replace
import os

import pytest

from config import load_settings
from database.database_manager import DatabaseManager, save_user_face_data
from database.models import DeviceState, InteractionLog, SystemEvent, UserRecord
from database.supabase_client import load_supabase_config


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self._operation = "select"
        self._payload = None
        self._filters = []
        self._limit = None

    def select(self, _columns):
        self._operation = "select"
        return self

    def eq(self, column, value):
        self._filters.append(("eq", column, value))
        return self

    def ilike(self, column, value):
        self._filters.append(("ilike", column, value))
        return self

    def limit(self, count):
        self._limit = count
        return self

    def insert(self, payload):
        self._operation = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._operation = "update"
        self._payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self._operation = "upsert"
        self._payload = payload
        self.client.upsert_conflicts.append(on_conflict)
        return self

    def execute(self):
        if self._operation == "insert":
            payload = dict(self._payload)
            payload.setdefault("id", f"{self.name}-{len(self.client.rows.get(self.name, [])) + 1}")
            self.client.rows.setdefault(self.name, []).append(payload)
            self.client.inserted.setdefault(self.name, []).append(payload)
            return FakeResponse([payload])

        if self._operation == "upsert":
            self.client.upserted.setdefault(self.name, []).append(self._payload)
            return FakeResponse([self._payload])

        rows = self._filtered_rows()
        if self._operation == "update":
            updated_rows = []
            for row in rows:
                row.update(self._payload)
                updated_rows.append(dict(row))
            self.client.updated.setdefault(self.name, []).extend(updated_rows)
            return FakeResponse(updated_rows)

        return FakeResponse(rows)

    def _filtered_rows(self):
        rows = list(self.client.rows.get(self.name, []))
        for kind, column, value in self._filters:
            if kind == "eq":
                rows = [row for row in rows if row.get(column) == value]
            elif kind == "ilike":
                rows = [
                    row
                    for row in rows
                    if str(row.get(column, "")).lower() == str(value).lower()
                ]
        if self._limit is not None:
            rows = rows[: self._limit]
        return rows


class FakeSupabaseClient:
    def __init__(self):
        self.rows = {
            "users": [
                {
                    "id": "user-1",
                    "created_at": "2026-01-01T00:00:00Z",
                    "full_name": "Karim Hassan",
                    "display_name": "Karim",
                    "is_authorized": True,
                    "face_label": "karim",
                    "face_embedding_path": "data/faces/Karim/karim_1.jpg",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "user-2",
                    "created_at": "2026-01-01T00:00:00Z",
                    "full_name": "Guest User",
                    "display_name": "Guest",
                    "is_authorized": False,
                    "face_label": "guest",
                    "face_embedding_path": None,
                    "updated_at": "2026-01-01T00:00:00Z",
                },
            ],
            "command_logs": [],
            "device_state": [],
        }
        self.inserted = {}
        self.updated = {}
        self.upserted = {}
        self.upsert_conflicts = []

    def table(self, name):
        return FakeTable(self, name)


def test_load_supabase_config_from_environment(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "secret-key")
    monkeypatch.setenv("SUPABASE_TIMEOUT_SECONDS", "3")

    config = load_supabase_config()

    assert config.configured is True
    assert config.url == "https://example.supabase.co"
    assert config.key == "secret-key"
    assert config.timeout_seconds == 3


def test_database_manager_connection_and_select():
    settings = replace(load_settings(), database_enabled=True, database_sync_users=True)
    manager = DatabaseManager(settings=settings, client=FakeSupabaseClient())

    health = manager.health_check()
    users = manager.get_authorized_users()

    assert health.reachable is True
    assert [user.name for user in users] == ["Karim"]


def test_database_manager_upserts_user_to_team_schema():
    settings = replace(load_settings(), database_enabled=True)
    fake_client = FakeSupabaseClient()
    manager = DatabaseManager(settings=settings, client=fake_client)

    user = manager.upsert_user(
        name="admin",
        authorized=True,
        face_image_path="data/faces/Admin/admin_1.jpg",
    )

    assert user is not None
    assert user.name == "Admin"
    inserted = fake_client.inserted["users"][0]
    assert inserted["display_name"] == "Admin"
    assert inserted["is_authorized"] is True
    assert inserted["face_label"] == "admin"
    assert inserted["face_embedding_path"] == "data/faces/Admin/admin_1.jpg"


def test_save_user_face_data_updates_existing_user_with_normalized_path():
    settings = replace(load_settings(), database_enabled=True)
    fake_client = FakeSupabaseClient()
    manager = DatabaseManager(settings=settings, client=fake_client)
    image_path = settings.project_root / "data" / "faces" / "Karim" / "karim_2.jpg"

    user = save_user_face_data(
        display_name="Karim",
        full_name="Karim Hassan",
        face_image_path=image_path,
        face_label="karim",
        database=manager,
    )

    assert user is not None
    assert user.id == "user-1"
    updated = fake_client.updated["users"][0]
    assert updated["display_name"] == "Karim"
    assert updated["full_name"] == "Karim Hassan"
    assert updated["face_label"] == "karim"
    assert updated["face_embedding_path"] == "data/faces/Karim/karim_2.jpg"


def test_database_manager_logs_command_event_and_device_state():
    settings = replace(
        load_settings(),
        database_enabled=True,
        database_log_commands=True,
        database_log_events=True,
        device_name="orb_test",
    )
    fake_client = FakeSupabaseClient()
    manager = DatabaseManager(settings=settings, client=fake_client)

    logged_interaction = manager.log_interaction(
        user_name="Karim",
        command="system status",
        ai_response="System online.",
        detected_intent="system_status",
        source="mock",
    )
    logged_event = manager.log_event("startup", "ORB started")

    assert logged_interaction is True
    assert logged_event is True
    command_log = fake_client.inserted["command_logs"][0]
    event_log = fake_client.inserted["command_logs"][1]
    assert command_log["user_id"] == "user-1"
    assert command_log["raw_command"] == "system status"
    assert command_log["detected-intent"] == "system_status"
    assert command_log["response_text"] == "System online."
    assert command_log["source"] == "mock"
    assert event_log["source"] == "system"
    assert event_log["status"] == "event"
    assert fake_client.rows["device_state"][0]["device_name"] == "orb_test"
    assert fake_client.rows["device_state"][0]["current_state"] == "startup"


def test_database_models_serialize_team_schema_payloads():
    user = UserRecord(id=None, name="Karim", authorized=True)
    interaction = InteractionLog(
        user_id=None,
        command="hello",
        ai_response="hi",
        detected_intent="greeting",
    )
    event = SystemEvent(event_type="test", message="ok")
    state = DeviceState(device_name="orb_test", current_state="idle")

    user_payload = user.to_insert_dict()
    interaction_payload = interaction.to_insert_dict()

    assert "id" not in user_payload
    assert "authorized" not in user_payload
    assert user_payload["is_authorized"] is True
    assert interaction_payload["raw_command"] == "hello"
    assert interaction_payload["detected-intent"] == "greeting"
    assert interaction_payload["user_id"] is None
    event_payload = event.to_insert_dict()
    state_payload = state.to_insert_dict()
    assert event_payload["source"] == "system"
    assert event_payload["user_id"] is None
    assert state_payload["device_name"] == "orb_test"
    assert "current_user_id" not in state_payload


@pytest.mark.skipif(
    os.getenv("ORB_RUN_SUPABASE_TESTS") != "1",
    reason="Set ORB_RUN_SUPABASE_TESTS=1 with real Supabase keys to run.",
)
@pytest.mark.supabase
def test_live_supabase_connection():
    manager = DatabaseManager(settings=load_settings())

    health = manager.health_check()

    assert health.reachable is True, health.message
