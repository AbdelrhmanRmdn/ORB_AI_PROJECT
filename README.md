# ORB AI Assistant

ORB is an offline-first embedded AI assistant prepared for Raspberry Pi 5. The runtime pipeline is:

1. YOLOv8n checks the camera feed for a person.
2. A frame is passed to face recognition.
3. If the face is authorized, faster-whisper records and transcribes speech.
4. The intent system generates a response.
5. pyttsx3 speaks the response offline.
6. If Supabase is configured, ORB syncs authorized users and logs commands/events.

The project defaults to mock mode so `python main.py` can start on a development machine without a camera, microphone, Pi GPIO, or downloaded models.

## Project Structure

```text
main.py                  CLI entry point
orb_pipeline.py          Full camera -> face -> speech -> AI -> TTS workflow
config.py                Environment-driven Raspberry Pi settings
intent_handler.py        Lightweight deterministic intent classifier
response_generator.py    Assistant responses
camera.py                Camera abstraction with mock mode
yolo_detector.py         YOLOv8n person-only detector
face_rec.py              Known-face loading and recognition
speech_to_text.py        faster-whisper microphone STT
text_to_speech.py        pyttsx3 offline TTS
led_control.py           Raspberry Pi LED ring control with mock fallback
database/                Supabase client, models, queries, schema, and manager
tests/                   Mock-safe tests plus optional hardware smoke tests
data/faces/              Put authorized face images here
data/models/             Local model cache
data/recordings/         Temporary microphone recordings
scripts/                 Pi setup and mock check helpers
```

## Quick Development Run

```bash
python -m pip install -r requirements.txt
python main.py --once --mock-command "system status" --non-interactive
python -m pytest
```

Interactive mock mode:

```bash
python main.py --mock
```

Real hardware mode:

```bash
python main.py --real
```

Terminal-only full pipeline simulation:

```bash
python simulation_mode.py --user Boudy
```

Non-interactive simulation:

```bash
python simulation_mode.py --user Boudy --command "hello" --command "what time is it" --command "exit"
```

Final system check:

```bash
python final_system_check.py
```

## Raspberry Pi 5 Setup

On the Raspberry Pi:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev build-essential cmake pkg-config libopenblas-dev liblapack-dev libjpeg-dev libpng-dev portaudio19-dev espeak-ng libatlas-base-dev libhdf5-dev libcamera-apps
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Or run:

```bash
bash scripts/bootstrap_pi.sh
```

`face-recognition` depends on `dlib`, which can take a long time to build on Raspberry Pi. Keep the Pi powered and cooled during installation.

## Configuration

Copy `.env.example` to `.env` and edit values:

```bash
cp .env.example .env
```

Important options:

```text
ORB_TEST_MODE=0
ORB_AUTHORIZED_USERS=Karim,Admin
ORB_WHISPER_MODEL_SIZE=tiny
ORB_YOLO_MODEL=yolov8n.pt
ORB_CAMERA_INDEX=0
ORB_LED_ENABLED=1
SUPABASE_URL=
SUPABASE_KEY=
ORB_DATABASE_ENABLED=1
ORB_DATABASE_SYNC_USERS=1
ORB_DATABASE_SYNC_FACE_METADATA=0
ORB_DATABASE_LOG_COMMANDS=1
ORB_DATABASE_LOG_EVENTS=1
```

Use `ORB_TEST_MODE=1` for mock demos and `ORB_TEST_MODE=0` on Raspberry Pi hardware.

## Face Images

Place authorized user images in `data/faces/`.

Recommended layout:

```text
data/faces/Karim/karim_1.jpg
data/faces/Karim/karim_2.jpg
data/faces/Admin/admin_1.jpg
```

Folder names become the recognized names. If images are placed directly in `data/faces/`, the file name is used. Each image should contain one clear frontal face.

## Supabase Integration

Supabase files live in `database/`.

- `database/supabase_client.py` creates the Supabase client from `SUPABASE_URL` and `SUPABASE_KEY`.
- `database/models.py` contains typed row models.
- `database/queries.py` contains table constants and schema SQL.
- `database/database_manager.py` is the only database layer the assistant pipeline calls.
- `database/schema.sql` is the SQL your software team should run in the Supabase SQL editor.

The assistant communicates with Supabase through `DatabaseManager`:

- During startup, it checks database health and logs a `startup` event.
- Face recognition can fetch authorized users from the `users` table.
- Optional local face metadata sync can upsert records into `users`.
- Every recognized command can be inserted into `interaction_logs`.
- Startup, shutdown, unauthorized face, and voice timeout events can be inserted into `system_events`.

Suggested table relationships:

```text
users.id -> interaction_logs.user_id
users stores authorization and face image metadata.
interaction_logs stores recognized commands and AI responses.
system_events stores operational events independent of a user.
```

To configure Supabase:

1. Create a Supabase project.
2. Open the SQL editor.
3. Run the contents of `database/schema.sql`.
4. Add authorized users to the `users` table.
5. Put the project URL and API key in `.env`.

For a university prototype on Raspberry Pi, using the Supabase anon key is acceptable only if Row Level Security policies are configured safely. For unrestricted inserts/selects from a trusted private Pi, use a server-side key carefully and never commit it.

## Model Downloads

Models are lazy-loaded.

- faster-whisper downloads the configured model, default `tiny`, into `data/models/faster-whisper/`.
- Ultralytics downloads `yolov8n.pt` on first real YOLO run. If a downloaded file appears in the project root, the detector copies it into `data/models/yolov8n.pt`.

For Raspberry Pi performance, the defaults use CPU, `int8` Whisper compute, low camera resolution, YOLO image size 320, and frame skipping.

## Optional Wheel Cache

A wheel cache is architecture-specific. Build it on the Raspberry Pi, not Windows:

```bash
bash scripts/cache_wheels_pi.sh
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

You can transfer `wheelhouse/` with the project for repeated installs on the same Pi OS/Python/architecture.

## Hardware Notes

- Microphone: install and test a USB microphone or Pi-compatible input device. `sounddevice` requires PortAudio.
- TTS: `pyttsx3` uses `espeak-ng` on Linux.
- Camera: enable and verify the camera before running real mode.
- LED ring: `rpi-ws281x` usually needs appropriate GPIO permissions or sudo depending on wiring and OS setup.

## Tests

Mock-safe tests:

```bash
python -m pytest
```

Optional Pi hardware smoke tests:

```bash
ORB_RUN_HARDWARE_TESTS=1 ORB_TEST_MODE=0 python -m pytest -m hardware
```

Optional live Supabase test:

```bash
ORB_RUN_SUPABASE_TESTS=1 python -m pytest tests/test_supabase.py -m supabase
```

Final Raspberry Pi release check after hardware and dependencies are installed:

```bash
python final_system_check.py --real --load-models --strict
```

## Transfer To Raspberry Pi

1. Copy the project folder to the Pi.
2. Create `.env` from `.env.example`.
3. Put face images into `data/faces/`.
4. Run `bash scripts/bootstrap_pi.sh`.
5. Activate the environment with `source .venv/bin/activate`.
6. Run `python main.py --real`.
