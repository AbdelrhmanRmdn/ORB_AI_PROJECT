from __future__ import annotations


USERS_TABLE = "users"
INTERACTION_LOGS_TABLE = "interaction_logs"
SYSTEM_EVENTS_TABLE = "system_events"

USER_COLUMNS = "id,name,authorized,face_image_path,created_at"
INTERACTION_LOG_COLUMNS = "id,user_id,command,ai_response,timestamp"
SYSTEM_EVENT_COLUMNS = "id,event_type,message,timestamp"

SUPABASE_SCHEMA_SQL = """
create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    authorized boolean not null default true,
    face_image_path text,
    created_at timestamptz not null default now()
);

create table if not exists public.interaction_logs (
    id bigint generated always as identity primary key,
    user_id uuid references public.users(id) on delete set null,
    command text not null,
    ai_response text not null,
    timestamp timestamptz not null default now()
);

create table if not exists public.system_events (
    id bigint generated always as identity primary key,
    event_type text not null,
    message text not null,
    timestamp timestamptz not null default now()
);

create index if not exists idx_users_authorized on public.users(authorized);
create index if not exists idx_interaction_logs_user_id on public.interaction_logs(user_id);
create index if not exists idx_interaction_logs_timestamp on public.interaction_logs(timestamp desc);
create index if not exists idx_system_events_timestamp on public.system_events(timestamp desc);
"""
