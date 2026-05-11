from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import replace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a terminal-only simulation of the ORB AI pipeline."
    )
    parser.add_argument("--user", default="Boudy", help="Simulated authorized user")
    parser.add_argument(
        "--command",
        action="append",
        help="Run one or more commands non-interactively, then exit",
    )
    parser.add_argument(
        "--log-database",
        action="store_true",
        help="Log simulated interactions to Supabase if configured",
    )
    return parser.parse_args()


def run_simulation(
    user: str = "Boudy",
    commands: Iterable[str] | None = None,
    log_database: bool = False,
    use_gemini: bool = True,
) -> int:
    from config import load_settings
    from database.database_manager import DatabaseManager
    from logging_config import configure_logging
    from response_generator import ResponseGenerator

    base_settings = load_settings()
    settings = replace(
        base_settings,
        test_mode=True,
        database_log_commands=log_database,
        database_log_events=log_database,
        llm_provider="gemini" if use_gemini else base_settings.llm_provider,
    )
    configure_logging(settings)
    database = DatabaseManager(settings)
    responses = ResponseGenerator(settings=settings, prefer_llm_for_all=use_gemini)

    print("=== ORB AI Assistant Terminal Simulation ===")
    if use_gemini:
        print(f"[AI MODEL] Gemini active: {settings.gemini_model}")
    print("[YOLO] Person detected")
    print(f"[FACE] Authorized user: {user}")
    print("[VOICE] Terminal speech input active")
    print("Type 'exit' to stop.\n")

    scripted_commands = list(commands or [])
    interactive = not scripted_commands

    while True:
        if scripted_commands:
            command = scripted_commands.pop(0).strip()
            print(f"You: {command}")
        else:
            try:
                command = input("You: ").strip()
            except EOFError:
                print()
                break

        if not command:
            print("[AI]: I did not hear a command.")
            if not interactive:
                break
            continue

        response = responses.generate(command, current_user=user)
        print(f"[AI]: {response.text}")
        print(f"[TTS SIM]: {response.text}\n")

        if log_database:
            logged = database.log_interaction(
                user,
                command,
                response.text,
                detected_intent=response.intent.name,
                source="simulation",
                status="shutdown_requested" if response.should_shutdown else "success",
            )
            print(f"[DB]: interaction logged={logged}")

        if response.should_shutdown:
            break

        if not interactive and not scripted_commands:
            break

    print("[SYSTEM] Simulation ended")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run_simulation(
            user=args.user,
            commands=args.command,
            log_database=args.log_database,
        )
    )


if __name__ == "__main__":
    main()
