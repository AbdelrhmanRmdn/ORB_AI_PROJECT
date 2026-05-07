from __future__ import annotations

import argparse
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ORB AI Assistant")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mock", action="store_true", help="Force mock mode")
    mode.add_argument("--real", action="store_true", help="Force real hardware/model mode")
    parser.add_argument("--once", action="store_true", help="Run one pipeline cycle and exit")
    parser.add_argument(
        "--mock-command",
        help="Command text to inject in mock mode, useful for tests and demos",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt for typed commands in mock mode",
    )
    return parser.parse_args()


def apply_cli_env(args: argparse.Namespace) -> None:
    if args.mock:
        os.environ["ORB_TEST_MODE"] = "1"
    if args.real:
        os.environ["ORB_TEST_MODE"] = "0"
    if args.once:
        os.environ["ORB_ONCE"] = "1"
    if args.mock_command:
        os.environ["ORB_MOCK_COMMAND"] = args.mock_command
    if args.non_interactive:
        os.environ["ORB_NONINTERACTIVE"] = "1"


def main() -> None:
    args = parse_args()
    apply_cli_env(args)

    from config import load_settings
    from logging_config import configure_logging
    from orb_pipeline import ORBAssistant

    settings = load_settings()
    configure_logging(settings)
    assistant = ORBAssistant(settings=settings, mock_command=args.mock_command)
    assistant.run(max_cycles=1 if settings.loop_once else None)


if __name__ == "__main__":
    main()
