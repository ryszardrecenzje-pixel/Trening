"""Prosty system tłumaczeń PL / EN."""

from __future__ import annotations

from typing import Dict

TEXTS: Dict[str, Dict[str, str]] = {
    "app_title": {"pl": "Home Workout", "en": "Home Workout"},
    "nav_workout": {"pl": "🏋️ Trening", "en": "🏋️ Workout"},
    "nav_equipment": {"pl": "🛠️ Sprzęt", "en": "🛠️ Gear"},
    "nav_history": {"pl": "📜 Historia", "en": "📜 History"},
    "nav_more": {"pl": "⚙️ Więcej", "en": "⚙️ More"},
    "equipment_title": {"pl": "🛠️ Twój sprzęt", "en": "🛠️ Your equipment"},
    "equipment_hint": {
        "pl": "Zaznacz posiadany sprzęt – plany dostosują się automatycznie.",
        "en": "Select the gear you have – plans adapt automatically.",
    },
    "equipment_body_always": {
        "pl": "Masa własnego ciała jest zawsze dostępna.",
        "en": "Bodyweight is always available.",
    },
    "generator_title": {"pl": "🏋️ Generator treningu", "en": "🏋️ Workout generator"},
    "goal": {"pl": "Cel treningu", "en": "Goal"},
    "duration": {"pl": "Czas trwania", "en": "Duration"},
    "level": {"pl": "Poziom", "en": "Level"},
    "warmup": {"pl": "Rozgrzewka (3–4 min)", "en": "Warm-up (3–4 min)"},
    "generate": {"pl": "⚡ Generuj trening", "en": "⚡ Generate workout"},
    "start_workout": {"pl": "▶️ Rozpocznij trening", "en": "▶️ Start workout"},
    "save_favorite": {"pl": "⭐ Zapisz jako ulubiony", "en": "⭐ Save as favorite"},
    "favorites": {"pl": "Ulubione plany", "en": "Favorite plans"},
    "history_title": {"pl": "📜 Historia", "en": "📜 History"},
    "no_history": {
        "pl": "Brak historii. Ukończ pierwszy trening!",
        "en": "No history yet. Complete your first workout!",
    },
    "clear_history": {"pl": "🗑️ Wyczyść historię", "en": "🗑️ Clear history"},
    "stats_week": {"pl": "Ten tydzień", "en": "This week"},
    "stats_streak": {"pl": "Seria dni", "en": "Day streak"},
    "done": {"pl": "✅ Zrobione – następna", "en": "✅ Done – next"},
    "rest": {"pl": "⏱️ Przerwa", "en": "⏱️ Rest"},
    "skip_rest": {"pl": "⏭️ Pomiń przerwę", "en": "⏭️ Skip rest"},
    "start": {"pl": "▶️ Start", "en": "▶️ Start"},
    "resume": {"pl": "▶️ Wznów", "en": "▶️ Resume"},
    "stop": {"pl": "⏸️ Stop", "en": "⏸️ Stop"},
    "get_ready": {"pl": "Przygotuj się…", "en": "Get ready…"},
    "time_up": {"pl": "Czas minął!", "en": "Time's up!"},
    "bravo": {"pl": "🎉 Brawo!", "en": "🎉 Well done!"},
    "workout_complete": {"pl": "Trening ukończony", "en": "Workout complete"},
    "save_return": {"pl": "💾 Zapisz i wróć", "en": "💾 Save & return"},
    "rpe_label": {"pl": "Jak oceniasz intensywność? (RPE)", "en": "Rate intensity (RPE)"},
    "note_label": {"pl": "Notatka (opcjonalnie)", "en": "Note (optional)"},
    "onboarding_title": {"pl": "Witaj w Home Workout!", "en": "Welcome to Home Workout!"},
    "onboarding_1": {
        "pl": "1️⃣ Wybierz sprzęt, który masz w domu.",
        "en": "1️⃣ Select the equipment you have at home.",
    },
    "onboarding_2": {
        "pl": "2️⃣ Ustaw cel, czas i poziom – wygeneruj trening.",
        "en": "2️⃣ Set goal, time and level – generate a workout.",
    },
    "onboarding_3": {
        "pl": "3️⃣ Ćwicz z timerem i animacją. Historia zapisze się automatycznie.",
        "en": "3️⃣ Train with timer and animation. History saves automatically.",
    },
    "got_it": {"pl": "Rozumiem – zaczynam!", "en": "Got it – let's go!"},
    "sound": {"pl": "Dźwięki stopera", "en": "Timer sounds"},
    "language": {"pl": "Język", "en": "Language"},
    "export": {"pl": "📤 Eksportuj dane", "en": "📤 Export data"},
    "import": {"pl": "📥 Importuj dane", "en": "📥 Import data"},
    "safety": {"pl": "⚠️ Bezpieczeństwo", "en": "⚠️ Safety"},
    "alternative": {"pl": "Zamiennik", "en": "Alternative"},
    "reps": {"pl": "powtórzeń", "en": "reps"},
    "next": {"pl": "Następne", "en": "Next"},
    "preview_move": {"pl": "Podgląd ruchu", "en": "Movement preview"},
}


def t(key: str, lang: str = "pl") -> str:
    entry = TEXTS.get(key, {})
    return entry.get(lang) or entry.get("pl") or key
