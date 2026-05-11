from dataclasses import replace

from config import load_settings
from full_system_simulation import build_assistant
from orb_pipeline import ORBAssistant


def test_full_pipeline_mock_cycle():
    settings = replace(
        load_settings(),
        test_mode=True,
        loop_once=True,
        mock_person_detected=True,
        mock_user="Karim",
        database_enabled=False,
        conversation_cooldown_seconds=0,
    )
    assistant = ORBAssistant(settings=settings, mock_command="system status")

    result = assistant.run_once()
    assistant.shutdown()

    assert result.person_detected is True
    assert result.identity is not None
    assert result.identity.authorized is True
    assert result.command == "system status"
    assert result.response is not None
    assert result.response.intent.name == "system_status"


def test_full_system_simulation_runner_builds_pipeline():
    assistant = build_assistant(
        user="Karim",
        mock_command="exit",
        log_database=False,
    )

    result = assistant.run_once()
    assistant.shutdown()

    assert result.person_detected is True
    assert result.identity is not None
    assert result.identity.name == "Karim"
    assert result.command == "exit"
    assert result.shutdown_requested is True
