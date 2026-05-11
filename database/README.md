# Database Package

This folder contains the complete Supabase integration layer for ORB.

## Files

- `supabase_client.py`: loads `SUPABASE_URL` and `SUPABASE_KEY` from environment variables or `.env`, then creates the Supabase Python client lazily.
- `models.py`: typed dataclasses for rows ORB reads or writes: `UserRecord`, `InteractionLog`, `SystemEvent`, and `DeviceState`.
- `queries.py`: table names, selected column lists, and an embedded copy of the suggested SQL schema.
- `database_manager.py`: reusable repository layer used by the assistant. It fetches authorized users, syncs local face metadata, logs commands/events, and updates device state.
- `schema.sql`: SQL to run in the Supabase SQL editor before using the project.

The rest of the project should talk to `DatabaseManager`, not directly to the Supabase client.

Useful manager methods:

- `get_users()`
- `get_authorized_users()`
- `get_user_by_name(name)`
- `upsert_user(name, authorized, face_image_path)`
- `save_user_face_data(display_name, face_image_path, full_name, authorized, face_label)`
- `set_user_authorized(name, authorized)`
- `sync_local_face_metadata()`
- `log_interaction(user_name, command, ai_response, detected_intent, source, status)`
- `log_event(event_type, message)`
- `update_device_state(...)`

## Tables

The code maps to the Supabase tables from the team schema:

- `users`: `full_name`, `display_name`, `is_authorized`, `face_label`, and `face_embedding_path`.
- `command_logs`: `user_id`, `raw_command`, `detected-intent`, `response_text`, `source`, and `status`.
- `device_state`: one row per device name, including the latest user, command, response, online flag, and state.
- `commands` and `command_keywords`: the configured intent vocabulary.
- `responses_manual_actions`: manual response/action rows.
- `system_settings`: configurable key/value settings.

System events are stored in `command_logs` with `source='system'` because the current team schema does not include a separate `system_events` table.

## Saving Face Data From Code

When another part of the project captures or chooses a user's face image, call the helper function instead of writing Supabase code there:

```python
from database import save_user_face_data

image_path = "data/faces/Karim/karim_2.jpg"

user = save_user_face_data(
    display_name="Karim",
    full_name="Karim Hassan",
    face_image_path=image_path,
    authorized=True,
    face_label="karim",
)

if user is None:
    print("Face data was not saved")
```

This writes to `public.users` and stores the image path in `face_embedding_path`.

If Supabase is not configured, the manager returns safe offline values and the assistant continues running locally.

## Supabase Setup

1. Create the Supabase project.
2. Open the SQL editor.
3. Run `database/schema.sql`.
4. Insert rows into `public.users` for each authorized person.
5. Copy the project URL and API key into `.env`.

Example user row:

```sql
insert into public.users (
    full_name,
    display_name,
    is_authorized,
    face_label,
    face_embedding_path
)
values (
    'Karim Hassan',
    'Karim',
    true,
    'karim',
    'data/faces/Karim/karim_1.jpg'
);
```

## Security

Do not commit `.env`. The project reads `SUPABASE_URL` and `SUPABASE_KEY` at runtime. If the Pi uses a Supabase anon key, enable Row Level Security and add policies that allow only the exact reads/inserts this assistant needs. If the software team chooses a service-role key for a private prototype, keep it only on the Raspberry Pi and never expose it to a browser or repository.
