$ErrorActionPreference = "Stop"
$env:ORB_TEST_MODE = "1"
python main.py --once --mock-command "system status" --non-interactive
