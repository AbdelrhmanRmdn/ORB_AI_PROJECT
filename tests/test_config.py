from config import load_settings


def test_load_settings_reads_current_environment(monkeypatch):
    monkeypatch.setenv("ORB_MOCK_USER", "Boudy")
    monkeypatch.setenv("ORB_DATABASE_LOG_COMMANDS", "0")

    settings = load_settings()

    assert settings.mock_user == "Boudy"
    assert settings.database_log_commands is False
