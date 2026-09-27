# 🏋️ Home Workout – Trening w domu

Streamlit + opcjonalnie **Supabase** (historia, ulubione, ustawienia).

## Funkcje

- Plany dopasowane do sprzętu, GIF-y, stoper (Start/Stop + 3 s)
- Rozgrzewka, ulubione, RPE, streak, PL/EN
- **Supabase** albo lokalny JSON (fallback)
- Eksport/import backupu

## Szybki start (lokalnie)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Bez secrets działa w trybie **local JSON**.

## Podłączenie Supabase

### 1. Projekt i tabele

1. [supabase.com](https://supabase.com) → New project  
2. **SQL Editor** → wklej `supabase/schema.sql` → **Run**

### 2. Klucze API

**Project Settings → API**:
- Project URL  
- `anon` `public` key  

### 3a. Streamlit Cloud

**Settings → Secrets**:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
anon_key = "eyJ..."
```

Reboot app.

### 3b. Lokalnie

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# uzupełnij url i anon_key
```

W aplikacji: **Więcej → Baza danych** pokaże status połączenia.

## Auth (później)

Tabele mają kolumnę `user_id` (nullable).  
Obecnie dane są wiązane z `client_id` (UUID urządzenia).  
Po dodaniu logowania: zapis `auth.uid()` + zaostrzenie RLS.

## Struktura

```
app.py
data/exercises.py
utils/
  storage.py          # Supabase + JSON fallback
  supabase_client.py
  workout.py audio.py i18n.py
supabase/schema.sql
.streamlit/secrets.toml.example
```

## requirements

```
streamlit==1.39.0
supabase==2.10.0
```
