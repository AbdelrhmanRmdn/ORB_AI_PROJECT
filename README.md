# ORB AI Assistant

ORB is a Raspberry Pi-ready AI assistant. It detects a person, recognizes an authorized face, listens to a voice command, generates a response, speaks it back, and syncs important activity to Supabase.

The project can run in mock/simulation mode on a laptop, then move to Raspberry Pi for camera, microphone, speaker, LED, YOLO, Whisper, and face recognition.

## What It Does

1. Detects a person with YOLO.
2. Recognizes the user with face recognition.
3. Checks if the user is authorized.
4. Converts speech to text with faster-whisper.
5. Classifies the command and generates a response.
6. Speaks the response with pyttsx3.
7. Sends command history, events, users, and device state to Supabase.
8. Can use Gemini/OpenAI/Ollama for fallback AI answers.

## Main Files

```text
main.py                  Main app runner
orb_pipeline.py          Full assistant flow
full_system_simulation.py Full terminal simulation using the real pipeline
simulation_mode.py       Terminal-only simulation
final_system_check.py    Final readiness checker
config.py                Environment settings
intent_handler.py        Command intent detection
response_generator.py    Response generation
face_rec.py              Face recognition
speech_to_text.py        Speech-to-text
text_to_speech.py        Text-to-speech
yolo_detector.py         Person detection
led_control.py           Raspberry Pi LED control
database/                Supabase integration
ai/                      Optional cloud/local LLM providers
tests/                   Automated tests
data/faces/              Authorized face images
```

The file that sends data to Supabase is:

```text
database/database_manager.py
```

## Quick Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in private values:

```bash
cp .env.example .env
```

Important `.env` values:

```text
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
ORB_DEVICE_NAME=orb_pi
ORB_TEST_MODE=1
ORB_DATABASE_ENABLED=1
ORB_LLM_PROVIDER=none
```

Use `ORB_TEST_MODE=1` for laptop demos and `ORB_TEST_MODE=0` on Raspberry Pi real hardware. `simulation_mode.py` forces Gemini for simulation responses even if `ORB_LLM_PROVIDER` is set to `none`.

## Run The Whole System In Terminal

This is the best command for your laptop presentation. It runs the full assistant pipeline in simulation mode:

```bash
python full_system_simulation.py
```

What it simulates:

```text
YOLO person detection
face recognition
typed terminal voice command
Gemini AI response
TTS speaking simulation
Supabase command/event/device logging
```

Type commands in the terminal when it says `Type command:`. Type `exit` to stop.

To run the same full system without Supabase writes:

```bash
python full_system_simulation.py --no-database
```

To quick-check one command:

```bash
python full_system_simulation.py --mock-command "explain embedded AI in one short sentence"
```

## Run A Smaller Terminal Simulation

Simulation uses Gemini by default. Best command for a Gemini terminal demo:

```bash
python simulation_mode.py --user Karim --command "explain embedded AI in one short sentence" --command "hello" --command "exit"
```

To also log the Gemini simulation to Supabase:

```bash
python simulation_mode.py --user Karim --log-database --command "explain embedded AI in one short sentence" --command "exit"
```

Alternative mock pipeline run:

```bash
python main.py --mock --once --mock-command "system status" --non-interactive
```

Run the Flask dashboard:

```bash
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Then open:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/command-logs
```

## Run On Raspberry Pi

Do not transfer the Windows `.venv` to the Pi. Copy the project folder, then create a fresh Pi virtual environment:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev build-essential cmake pkg-config libopenblas-dev liblapack-dev libjpeg-dev libpng-dev portaudio19-dev espeak-ng libatlas-base-dev libhdf5-dev libcamera-apps
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python main.py --real
```

You can also run:

```bash
bash scripts/bootstrap_pi.sh
```

## Supabase Tables

The code matches the team Supabase schema:

```text
users
command_logs
device_state
commands
command_keywords
system_settings
responses_manual_actions
```

Connected data:

```text
users                  Authorized users and face image paths
command_logs           Commands, detected intent, responses, events
device_state           Latest device/user/command/response state
commands               Intent definitions from Supabase
command_keywords       Keywords linked to commands
system_settings        Team settings table
responses_manual_actions Manual response/action table
```

Important note: the command intent column is named `detected-intent` in Supabase, with a hyphen. The code already handles this.

## Save Face Data To Supabase

When code captures or chooses a user image, call:

```python
from database import save_user_face_data

save_user_face_data(
    display_name="Karim",
    full_name="Karim Hassan",
    face_image_path="data/faces/Karim/karim_2.jpg",
    authorized=True,
    face_label="karim",
)
```

This writes to `users.face_embedding_path`. The actual image file stays in the project folder unless Supabase Storage upload is added later.

## Face Images

Put authorized face images here:

```text
data/faces/Karim/karim_1.jpg
data/faces/Karim/karim_2.jpg
data/faces/Admin/admin_1.jpg
```

Each image should contain one clear frontal face.

## Tests And Final Checks

Run all mock-safe tests:

```bash
python -m pytest
```

Run final project check:

```bash
python final_system_check.py
```

Run live Supabase test:

```bash
ORB_RUN_SUPABASE_TESTS=1 python -m pytest tests/test_supabase.py -m supabase
```

On Raspberry Pi, after hardware is connected:

```bash
python final_system_check.py --real --load-models --strict
```

## Presentation Summary

ORB AI is an embedded assistant prepared for Raspberry Pi. It supports camera/person detection, face authorization, speech-to-text, intent handling, spoken responses, optional LLM fallback, and Supabase logging. Supabase stores users, command history, system events, and device state using the team’s database schema. The project is ready for laptop simulation and Raspberry Pi deployment after installing Pi dependencies and configuring `.env`.
