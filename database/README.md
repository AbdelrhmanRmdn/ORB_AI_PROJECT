# Database Package

This folder contains the complete Supabase integration layer for ORB.

## Files

- `supabase_client.py`: loads `SUPABASE_URL` and `SUPABASE_KEY` from environment variables or `.env`, then creates the Supabase Python client lazily.
- `models.py`: typed dataclasses for rows ORB reads or writes: `UserRecord`, `InteractionLog`, and `SystemEvent`.
- `queries.py`: table names, selected column lists, and an embedded copy of the suggested SQL schema.
- `database_manager.py`: reusable repository layer used by the assistant. It fetches authorized users, syncs local face metadata, logs commands, and logs system events.
- `schema.sql`: SQL to run in the Supabase SQL editor before using the project.

The rest of the project should talk to `DatabaseManager`, not directly to the Supabase client.

Useful manager methods:

- `get_users()`
- `get_authorized_users()`
- `get_user_by_name(name)`
- `upsert_user(name, authorized, face_image_path)`
- `set_user_authorized(name, authorized)`
- `sync_local_face_metadata()`
- `log_interaction(user_name, command, ai_response)`
- `log_event(event_type, message)`

## Tables

`users` stores who can use the assistant. `interaction_logs.user_id` references `users.id`, so command history can be connected to a known authorized person. `system_events` stores operational events such as startup, shutdown, and unauthorized access.

If Supabase is not configured, the manager returns safe offline values and the assistant continues running locally.

## Supabase Setup

1. Create the Supabase project.
2. Open the SQL editor.
3. Run `database/schema.sql`.
4. Insert rows into `public.users` for each authorized person.
5. Copy the project URL and API key into `.env`.

Example user row:

```sql
insert into public.users (name, authorized, face_image_path)
values ('Karim', true, 'data/faces/Karim/karim_1.jpg');
```

## Security

Do not commit `.env`. The project reads `SUPABASE_URL` and `SUPABASE_KEY` at runtime. If the Pi uses a Supabase anon key, enable Row Level Security and add policies that allow only the exact reads/inserts this assistant needs. If the software team chooses a service-role key for a private prototype, keep it only on the Raspberry Pi and never expose it to a browser or repository.
