from __future__ import annotations

import argparse
from dataclasses import replace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full ORB pipeline in terminal simulation mode with Gemini."
    )
    parser.add_argument("--user", default="Karim", help="Simulated recognized user")
    parser.add_argument(
        "--mock-command",
        help="Run one command without prompting, useful for quick checks",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one full pipeline cycle and exit",
    )
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="Do not write simulated events or commands to Supabase",
    )
    return parser.parse_args()


def build_assistant(
    user: str = "Karim",
    mock_command: str | None = None,
    log_database: bool = True,
):
    from config import load_settings
    from database.database_manager import DatabaseManager
    from logging_config import configure_logging
    from orb_pipeline import ORBAssistant
    from response_generator import ResponseGenerator

    base_settings = load_settings()
    settings = replace(
        base_settings,
        test_mode=True,
        mock_user=user,
        mock_person_detected=True,
        non_interactive=False,
        database_enabled=log_database,
        llm_provider="gemini",
        database_log_commands=log_database,
        database_log_events=log_database,
    )
    configure_logging(settings)

    responses = ResponseGenerator(settings=settings, prefer_llm_for_all=True)
    database = DatabaseManager(settings=settings)
    if log_database:
        user_record = database.upsert_user(name=user, authorized=True)
        if user_record and user_record.id:
            database.update_device_state(
                current_user_id=user_record.id,
                current_state="simulation_ready",
                is_online=True,
            )
    return ORBAssistant(
        settings=settings,
        responses=responses,
        database=database,
        mock_command=mock_command,
    )


def run_full_system_simulation(
    user: str = "Karim",
    mock_command: str | None = None,
    once: bool = False,
    log_database: bool = True,
) -> int:
    assistant = build_assistant(
        user=user,
        mock_command=mock_command,
        log_database=log_database,
    )
    print("=== ORB Full System Simulation ===")
    database_mode = "Supabase logging" if log_database else "database disabled"
    print(
        "[MODE] Full pipeline: YOLO mock -> face mock -> typed voice -> "
        f"Gemini -> TTS -> {database_mode}"
    )
    print("[AI MODEL] Gemini active")
    print("Type 'exit' when you want to stop.\n")

    max_cycles = 1 if once or mock_command else None
    assistant.run(max_cycles=max_cycles)
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run_full_system_simulation(
            user=args.user,
            mock_command=args.mock_command,
            once=args.once,
            log_database=not args.no_database,
        )
    )


if __name__ == "__main__":
    main()
