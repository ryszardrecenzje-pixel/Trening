-- Home Workout – schemat Supabase
-- Uruchom w: Supabase Dashboard → SQL Editor → New query → Run
-- Auth (user_id) dołożymy później – na razie identyfikacja po client_id (urządzenie).

-- ── Sesje treningowe ─────────────────────────────────────
create table if not exists public.workout_sessions (
  id text primary key,
  client_id text not null,
  user_id uuid null,  -- auth.users – później
  date timestamptz not null,
  duration_minutes int not null default 0,
  goal text,
  level text,
  exercises_completed int default 0,
  total_exercises int default 0,
  estimated_calories int default 0,
  workout_name text,
  rpe int null,
  note text default '',
  created_at timestamptz not null default now()
);

create index if not exists idx_sessions_client on public.workout_sessions (client_id);
create index if not exists idx_sessions_date on public.workout_sessions (date desc);

-- ── Ulubione plany ───────────────────────────────────────
create table if not exists public.favorites (
  id uuid primary key default gen_random_uuid(),
  client_id text not null,
  user_id uuid null,
  name text not null,
  goal text not null,
  duration int not null,
  level text not null,
  include_warmup boolean not null default false,
  created_at timestamptz not null default now(),
  unique (client_id, name)
);

create index if not exists idx_favorites_client on public.favorites (client_id);

-- ── Ustawienia aplikacji ─────────────────────────────────
create table if not exists public.app_settings (
  client_id text primary key,
  user_id uuid null,
  language text not null default 'pl',
  onboarding_done boolean not null default false,
  sound_enabled boolean not null default true,
  updated_at timestamptz not null default now()
);

-- ── RLS (MVP: dostęp anon; po auth zaostrzymy) ───────────
alter table public.workout_sessions enable row level security;
alter table public.favorites enable row level security;
alter table public.app_settings enable row level security;

-- Polityki: pełny dostęp dla roli anon + authenticated (do czasu auth)
-- UWAGA: to jest świadomie otwarte na MVP. Po dodaniu logowania
-- zamień na: using (auth.uid() = user_id OR client_id = ...).

drop policy if exists "sessions_all" on public.workout_sessions;
create policy "sessions_all" on public.workout_sessions
  for all using (true) with check (true);

drop policy if exists "favorites_all" on public.favorites;
create policy "favorites_all" on public.favorites
  for all using (true) with check (true);

drop policy if exists "settings_all" on public.app_settings;
create policy "settings_all" on public.app_settings
  for all using (true) with check (true);

-- Opcjonalnie: real-time (nie wymagane)
-- alter publication supabase_realtime add table public.workout_sessions;
