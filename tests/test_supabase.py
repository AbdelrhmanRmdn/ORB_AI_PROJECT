from dataclasses import replace
import os

import pytest

from config import load_settings
from database.database_manager import DatabaseManager
from database.models import InteractionLog, SystemEvent, UserRecord
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

    def select(self, _columns):
        self._operation = "select"
        return self

    def eq(self, column, value):
        self._filters.append(("eq", column, value))
        return self

    def ilike(self, column, value):
        self._filters.append(("ilike", column, value))
        return self

    def limit(self, _count):
        return self

    def insert(self, payload):
        self._operation = "insert"
        self._payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self._operation = "upsert"
        self._payload = payload
        self.client.upsert_conflicts.append(on_conflict)
        return self

    def execute(self):
        if self._operation == "insert":
            self.client.inserted.setdefault(self.name, []).append(self._payload)
            return FakeResponse([self._payload])
        if self._operation == "upsert":
            self.client.upserted.setdefault(self.name, []).append(self._payload)
            return FakeResponse([self._payload])

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
        return FakeResponse(rows)


class FakeSupabaseClient:
    def __init__(self):
        self.rows = {
            "users": [
                {
                    "id": "user-1",
                    "name": "Karim",
                    "authorized": True,
                    "face_image_path": "data/faces/Karim/karim_1.jpg",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "user-2",
                    "name": "Guest",
                    "authorized": False,
                    "face_image_path": None,
                    "created_at": "2026-01-01T00:00:00Z",
                },
            ]
        }
        self.inserted = {}
        self.upserted = {}
        self.upsert_conflicts = []

    def table(self, name):
        return FakeTable(self, name)


def test_load_supabase_config_from_environment(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "secret-key")

    config = load_supabase_config()

    assert config.configured is True
    assert config.url == "https://example.supabase.co"
    assert config.key == "secret-key"


def test_database_manager_connection_and_select():
    settings = replace(load_settings(), database_enabled=True, database_sync_users=True)
    manager = DatabaseManager(settings=settings, client=FakeSupabaseClient())

    health = manager.health_check()
    users = manager.get_authorized_users()

    assert health.reachable is True
    assert [user.name for user in users] == ["Karim"]


def test_database_manager_upserts_user():
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
    assert fake_client.upserted["users"][0]["authorized"] is True
    assert fake_client.upsert_conflicts == ["name"]


def test_database_manager_logs_interaction_and_event():
    settings = replace(
        load_settings(),
        database_enabled=True,
        database_log_commands=True,
        database_log_events=True,
    )
    fake_client = FakeSupabaseClient()
    manager = DatabaseManager(settings=settings, client=fake_client)

    logged_interaction = manager.log_interaction(
        user_name="Karim",
        command="system status",
        ai_response="System online.",
    )
    logged_event = manager.log_event("startup", "ORB started")

    assert logged_interaction is True
    assert logged_event is True
    assert fake_client.inserted["interaction_logs"][0]["user_id"] == "user-1"
    assert fake_client.inserted["interaction_logs"][0]["command"] == "system status"
    assert fake_client.inserted["system_events"][0]["event_type"] == "startup"


def test_database_models_serialize_clean_payloads():
    user = UserRecord(id=None, name="Karim", authorized=True)
    interaction = InteractionLog(user_id=None, command="hello", ai_response="hi")
    event = SystemEvent(event_type="test", message="ok")

    assert "id" not in user.to_insert_dict()
    assert "user_id" not in interaction.to_insert_dict()
    assert event.to_insert_dict()["event_type"] == "test"


@pytest.mark.skipif(
    os.getenv("ORB_RUN_SUPABASE_TESTS") != "1",
    reason="Set ORB_RUN_SUPABASE_TESTS=1 with real Supabase keys to run.",
)
@pytest.mark.supabase
def test_live_supabase_connection():
    manager = DatabaseManager(settings=load_settings())

    health = manager.health_check()

    assert health.reachable is True, health.message
