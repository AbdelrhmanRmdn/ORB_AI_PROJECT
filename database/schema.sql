create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    full_name text,
    display_name text,
    is_authorized boolean not null default true,
    face_label text,
    face_embedding_path text,
    updated_at timestamptz not null default now()
);

create table if not exists public.commands (
    id uuid primary key default gen_random_uuid(),
    intent_name text not null,
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists public.command_keywords (
    id uuid primary key default gen_random_uuid(),
    command_id uuid references public.commands(id) on delete cascade,
    keyword text not null,
    match_type text not null default 'contains',
    created_at timestamptz not null default now()
);

create table if not exists public.responses_manual_actions (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    response_text text not null,
    action_type text
);

create table if not exists public.command_logs (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    user_id uuid references public.users(id) on delete set null,
    raw_command text,
    "detected-intent" text,
    response_text text,
    source text,
    status text
);

create table if not exists public.device_state (
    id uuid primary key default gen_random_uuid(),
    device_name text not null,
    current_user_id uuid references public.users(id) on delete set null,
    is_online boolean not null default false,
    current_state text,
    last_command text,
    last_response text,
    updated_at timestamptz not null default now()
);

create table if not exists public.system_settings (
    id uuid primary key default gen_random_uuid(),
    setting_key text not null,
    setting_value text,
    description text,
    updated_at timestamptz not null default now()
);

create index if not exists idx_users_is_authorized on public.users(is_authorized);
create index if not exists idx_users_display_name on public.users(display_name);
create index if not exists idx_users_face_label on public.users(face_label);
create index if not exists idx_command_logs_user_id on public.command_logs(user_id);
create index if not exists idx_command_logs_created_at on public.command_logs(created_at desc);
create index if not exists idx_command_logs_detected_intent on public.command_logs("detected-intent");
create index if not exists idx_device_state_device_name on public.device_state(device_name);
create index if not exists idx_system_settings_setting_key on public.system_settings(setting_key);
create index if not exists idx_commands_intent_name on public.commands(intent_name);
create index if not exists idx_command_keywords_keyword on public.command_keywords(keyword);
