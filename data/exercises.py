"""Baza ćwiczeń domowych – min. 30 pozycji z filtrowaniem po sprzęcie."""

from typing import TypedDict, List, Literal

Equipment = Literal[
    "bodyweight",
    "dumbbells",
    "pullup_bar",
    "resistance_bands",
    "bench",
    "rings_trx",
    "jump_rope",
]

MuscleGroup = Literal[
    "chest", "back", "legs", "shoulders", "core", "arms", "cardio", "fullbody"
]

Difficulty = Literal["beginner", "intermediate", "advanced"]

EQUIPMENT_LABELS = {
    "bodyweight": "🧍 Masa własnego ciała",
    "dumbbells": "🏋️ Hantle / Kettlebell",
    "pullup_bar": "🆙 Drążek do podciągania",
    "resistance_bands": "🔗 Gumy oporowe",
    "bench": "🪑 Ławka / Krzesło",
    "rings_trx": "⭕ Kółka / TRX",
    "jump_rope": "🪢 Skakanka",
}

MUSCLE_GROUP_LABELS = {
    "chest": "Klatka",
    "back": "Plecy",
    "legs": "Nogi",
    "shoulders": "Barki",
    "core": "Brzuch",
    "arms": "Ramiona",
    "cardio": "Cardio",
    "fullbody": "Całe ciało",
}

GOAL_LABELS = {
    "fat_loss": "🔥 Spalanie tłuszczu",
    "strength": "💪 Budowa siły",
    "fullbody": "🎯 Obwód FBW",
    "endurance": "⚡ Wytrzymałość",
}

DIFFICULTY_LABELS = {
    "beginner": "Początkujący",
    "intermediate": "Średniozaawansowany",
    "advanced": "Zaawansowany",
}

EXERCISES = [
    # --- BODYWEIGHT / CHEST ---
    {
        "id": "pushup",
        "gif_url": "https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.1.0/pectorals/push-up.gif",
        "safety_tip": "Nie zapadaj klatki – ciało w jednej linii, łokcie ~45°.",
        "name_pl": "Pompki klasyczne",
        "muscle_group": "chest",
        "difficulty": "beginner",
        "equipment": ["bodyweight"],
        "instructions_pl": "Utrzymuj ciało prosto, opuść klatkę do podłogi, wypchnij w górę.",
        "default_reps": 12,
        "is_timed": False,
        "calories_per_min": 8,
    },
]

ALL_EQUIPMENT = list(EQUIPMENT_LABELS.keys())
