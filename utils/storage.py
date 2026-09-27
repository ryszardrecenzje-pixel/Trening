"""Trwały zapis historii, ulubionych i ustawień (JSON na dysku + eksport/import)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Katalog danych użytkownika (obok projektu)
DATA_DIR = Path(__file__).resolve().parent.parent / "user_data"
HISTORY_FILE = DATA_DIR / "history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


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


# ── Historia ──────────────────────────────────────────────

def load_history() -> List[Dict]:
    data = _read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


def save_history(history: List[Dict]) -> bool:
    return _write_json(HISTORY_FILE, history[:100])


def add_history_entry(history: List[Dict], entry: Dict) -> List[Dict]:
    updated = [entry] + history
    updated = updated[:100]
    save_history(updated)
    return updated


# ── Ulubione plany ────────────────────────────────────────

def load_favorites() -> List[Dict]:
    data = _read_json(FAVORITES_FILE, [])
    return data if isinstance(data, list) else []


def save_favorites(favorites: List[Dict]) -> bool:
    return _write_json(FAVORITES_FILE, favorites[:20])


def add_favorite(favorites: List[Dict], fav: Dict) -> List[Dict]:
    # unikaj duplikatów po nazwie
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

DEFAULT_SETTINGS = {
    "language": "pl",
    "onboarding_done": False,
    "sound_enabled": True,
}


def load_settings() -> Dict:
    data = _read_json(SETTINGS_FILE, {})
    if not isinstance(data, dict):
        data = {}
    merged = {**DEFAULT_SETTINGS, **data}
    return merged


def save_settings(settings: Dict) -> bool:
    return _write_json(SETTINGS_FILE, settings)


# ── Statystyki ────────────────────────────────────────────

def compute_stats(history: List[Dict]) -> Dict[str, Any]:
    """Statystyki ogólne + tydzień + streak."""
    total_sessions = len(history)
    total_minutes = sum(h.get("duration_minutes", 0) for h in history)
    total_calories = sum(h.get("estimated_calories", 0) for h in history)

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    week_sessions = []
    for h in history:
        try:
            dt = datetime.fromisoformat(h["date"])
            if dt >= week_ago:
                week_sessions.append(h)
        except (KeyError, ValueError):
            continue

    week_minutes = sum(h.get("duration_minutes", 0) for h in week_sessions)
    week_calories = sum(h.get("estimated_calories", 0) for h in week_sessions)

    # Streak: kolejne dni z ≥1 treningiem (od dziś wstecz)
    days_with_workout = set()
    for h in history:
        try:
            dt = datetime.fromisoformat(h["date"])
            days_with_workout.add(dt.date())
        except (KeyError, ValueError):
            continue

    streak = 0
    day = now.date()
    # jeśli dziś nie ma treningu, zacznij od wczoraj (streak nie musi pękać rano)
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
    """JSON do pobrania przez użytkownika."""
    payload = {
        "exported_at": datetime.now().isoformat(),
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
