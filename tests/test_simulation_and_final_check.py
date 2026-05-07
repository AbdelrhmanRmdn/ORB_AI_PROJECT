from final_system_check import FinalSystemChecker
from simulation_mode import run_simulation


def test_terminal_simulation_scripted_flow(capsys):
    exit_code = run_simulation(
        user="Boudy",
        commands=["hello", "what time is it", "exit"],
        log_database=False,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[YOLO] Person detected" in captured.out
    assert "[FACE] Authorized user: Boudy" in captured.out
    assert "[AI]: Hello Boudy" in captured.out


def test_final_system_checker_mock_mode_has_no_failures():
    checker = FinalSystemChecker(real=False, load_models=False, strict=False)
    exit_code = checker.run()

    assert exit_code == 0
    assert not any(result.status == "FAIL" for result in checker.results)
