"""
Trwały zapis: Supabase (priorytet) + fallback JSON na dysku.
Identyfikacja urządzenia: client_id (UUID) – do czasu logowania.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.supabase_client import get_supabase, is_supabase_configured, supabase_status

# ── Lokalny fallback ──────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "user_data"
HISTORY_FILE = DATA_DIR / "history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
CLIENT_ID_FILE = DATA_DIR / "client_id.txt"

DEFAULT_SETTINGS = {
    "language": "pl",
    "onboarding_done": False,
    "sound_enabled": True,
}


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    _ensure_dir()
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> bool:
    _ensure_dir()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ── client_id (urządzenie) ────────────────────────────────

def get_client_id() -> str:
    """Stabilny ID urządzenia – lokalny plik (i kopia w settings)."""
    _ensure_dir()
    if CLIENT_ID_FILE.exists():
        cid = CLIENT_ID_FILE.read_text(encoding="utf-8").strip()
        if cid:
            return cid
    cid = str(uuid.uuid4())
    try:
        CLIENT_ID_FILE.write_text(cid, encoding="utf-8")
    except OSError:
        pass
    return cid


def _use_sb() -> bool:
    return is_supabase_configured() and get_supabase() is not None


# ── Historia ──────────────────────────────────────────────

def load_history() -> List[Dict]:
    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            res = (
                sb.table("workout_sessions")
                .select("*")
                .eq("client_id", cid)
                .order("date", desc=True)
                .limit(100)
                .execute()
            )
            rows = res.data or []
            return [_session_from_row(r) for r in rows]
        except Exception:
            pass
    data = _read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


def save_history(history: List[Dict]) -> bool:
    """Pełny zapis listy – lokalnie zawsze; na SB: sync (delete+insert uproszczony nie)."""
    ok_local = _write_json(HISTORY_FILE, history[:100])
    # Na SB pojedyncze wpisy idą przez add_history_entry;
    # pełny save używamy głównie przy clear / import.
    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            # wyczyść sesje tego klienta i wstaw aktualne
            sb.table("workout_sessions").delete().eq("client_id", cid).execute()
            if history:
                rows = [_session_to_row(h, cid) for h in history[:100]]
                sb.table("workout_sessions").insert(rows).execute()
            return True
        except Exception:
            return ok_local
    return ok_local


def add_history_entry(history: List[Dict], entry: Dict) -> List[Dict]:
    updated = [entry] + list(history)
    updated = updated[:100]
    _write_json(HISTORY_FILE, updated)

    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            sb.table("workout_sessions").upsert(_session_to_row(entry, cid)).execute()
        except Exception:
            pass
    return updated


def _session_to_row(h: Dict, client_id: str) -> Dict:
    return {
        "id": h.get("id") or f"s-{uuid.uuid4()}",
        "client_id": client_id,
        "date": h.get("date") or datetime.now().isoformat(),
        "duration_minutes": int(h.get("duration_minutes") or 0),
        "goal": h.get("goal"),
        "level": h.get("level"),
        "exercises_completed": int(h.get("exercises_completed") or 0),
        "total_exercises": int(h.get("total_exercises") or 0),
        "estimated_calories": int(h.get("estimated_calories") or 0),
        "workout_name": h.get("workout_name"),
        "rpe": h.get("rpe"),
        "note": h.get("note") or "",
    }


def _session_from_row(r: Dict) -> Dict:
    return {
        "id": r.get("id"),
        "date": r.get("date"),
        "duration_minutes": r.get("duration_minutes", 0),
        "goal": r.get("goal"),
        "level": r.get("level"),
        "exercises_completed": r.get("exercises_completed", 0),
        "total_exercises": r.get("total_exercises", 0),
        "estimated_calories": r.get("estimated_calories", 0),
        "workout_name": r.get("workout_name"),
        "rpe": r.get("rpe"),
        "note": r.get("note") or "",
    }


# ── Ulubione ──────────────────────────────────────────────

def load_favorites() -> List[Dict]:
    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            res = (
                sb.table("favorites")
                .select("*")
                .eq("client_id", cid)
                .order("created_at", desc=True)
                .execute()
            )
            rows = res.data or []
            return [
                {
                    "name": r["name"],
                    "goal": r["goal"],
                    "duration": r["duration"],
                    "level": r["level"],
                    "include_warmup": r.get("include_warmup", False),
                }
                for r in rows
            ]
        except Exception:
            pass
    data = _read_json(FAVORITES_FILE, [])
    return data if isinstance(data, list) else []


def save_favorites(favorites: List[Dict]) -> bool:
    ok_local = _write_json(FAVORITES_FILE, favorites[:20])
    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            sb.table("favorites").delete().eq("client_id", cid).execute()
            if favorites:
                rows = [
                    {
                        "client_id": cid,
                        "name": f.get("name", "Plan"),
                        "goal": f.get("goal", "fullbody"),
                        "duration": int(f.get("duration") or 30),
                        "level": f.get("level", "intermediate"),
                        "include_warmup": bool(f.get("include_warmup", False)),
                    }
                    for f in favorites[:20]
                ]
                sb.table("favorites").insert(rows).execute()
            return True
        except Exception:
            return ok_local
    return ok_local


def add_favorite(favorites: List[Dict], fav: Dict) -> List[Dict]:
    name = fav.get("name", "")
    updated = [f for f in favorites if f.get("name") != name]
    updated.insert(0, fav)
    updated = updated[:20]
    save_favorites(updated)
    return updated


def remove_favorite(favorites: List[Dict], name: str) -> List[Dict]:
    updated = [f for f in favorites if f.get("name") != name]
    save_favorites(updated)
    return updated


# ── Ustawienia ────────────────────────────────────────────

def load_settings() -> Dict:
    local = _read_json(SETTINGS_FILE, {})
    if not isinstance(local, dict):
        local = {}
    merged = {**DEFAULT_SETTINGS, **local}

    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            res = (
                sb.table("app_settings")
                .select("*")
                .eq("client_id", cid)
                .limit(1)
                .execute()
            )
            if res.data:
                row = res.data[0]
                merged["language"] = row.get("language") or merged["language"]
                merged["onboarding_done"] = bool(
                    row.get("onboarding_done", merged["onboarding_done"])
                )
                merged["sound_enabled"] = bool(
                    row.get("sound_enabled", merged["sound_enabled"])
                )
        except Exception:
            pass
    return merged


def save_settings(settings: Dict) -> bool:
    data = {**DEFAULT_SETTINGS, **settings}
    ok_local = _write_json(SETTINGS_FILE, data)

    if _use_sb():
        try:
            sb = get_supabase()
            cid = get_client_id()
            row = {
                "client_id": cid,
                "language": data.get("language", "pl"),
                "onboarding_done": bool(data.get("onboarding_done", False)),
                "sound_enabled": bool(data.get("sound_enabled", True)),
                "updated_at": datetime.now().isoformat(),
            }
            sb.table("app_settings").upsert(row).execute()
            return True
        except Exception:
            return ok_local
    return ok_local


# ── Statystyki (bez zmian – na liście w pamięci) ──────────

def compute_stats(history: List[Dict]) -> Dict[str, Any]:
    total_sessions = len(history)
    total_minutes = sum(h.get("duration_minutes", 0) for h in history)
    total_calories = sum(h.get("estimated_calories", 0) for h in history)

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    week_sessions = []
    for h in history:
        try:
            dt = datetime.fromisoformat(str(h["date"]).replace("Z", "+00:00"))
            if dt.replace(tzinfo=None) >= week_ago:
                week_sessions.append(h)
        except (KeyError, ValueError, TypeError):
            continue

    week_minutes = sum(h.get("duration_minutes", 0) for h in week_sessions)
    week_calories = sum(h.get("estimated_calories", 0) for h in week_sessions)

    days_with_workout = set()
    for h in history:
        try:
            dt = datetime.fromisoformat(str(h["date"]).replace("Z", "+00:00"))
            days_with_workout.add(dt.date())
        except (KeyError, ValueError, TypeError):
            continue

    streak = 0
    day = now.date()
    if day not in days_with_workout:
        day = day - timedelta(days=1)
    while day in days_with_workout:
        streak += 1
        day = day - timedelta(days=1)

    return {
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_calories": total_calories,
        "week_sessions": len(week_sessions),
        "week_minutes": week_minutes,
        "week_calories": week_calories,
        "streak": streak,
    }


def export_all(history: List[Dict], favorites: List[Dict], settings: Dict) -> str:
    payload = {
        "exported_at": datetime.now().isoformat(),
        "client_id": get_client_id(),
        "history": history,
        "favorites": favorites,
        "settings": settings,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def import_all(raw: str) -> Optional[Dict]:
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return {
            "history": data.get("history") or [],
            "favorites": data.get("favorites") or [],
            "settings": {**DEFAULT_SETTINGS, **(data.get("settings") or {})},
        }
    except (json.JSONDecodeError, TypeError):
        return None


def get_backend_status() -> Dict[str, Any]:
    """Do UI – czy jesteśmy na Supabase."""
    status = supabase_status()
    status["client_id"] = get_client_id()[:8] + "…"
    return status
