"""Logika generowania treningu i filtrowania ćwiczeń."""

import random
from datetime import datetime
from typing import List, Dict, Any

from data.exercises import (
    EXERCISES,
    DIFFICULTY_LABELS,
    GOAL_LABELS,
)


def filter_by_equipment(available: List[str]) -> List[Dict]:
    """Zwraca tylko ćwiczenia, do których użytkownik ma cały wymagany sprzęt."""
    return [
        ex
        for ex in EXERCISES
        if all(eq in available for eq in ex["equipment"])
    ]


def filter_by_difficulty(exercises: List[Dict], level: str) -> List[Dict]:
    order = ["beginner", "intermediate", "advanced"]
    max_idx = order.index(level)
    return [ex for ex in exercises if order.index(ex["difficulty"]) <= max_idx]


def _get_rest_seconds(level: str) -> int:
    return {"beginner": 60, "intermediate": 45, "advanced": 30}[level]


def _get_sets(level: str, goal: str) -> int:
    if goal == "strength":
        return 3 if level == "beginner" else 4
    if goal in ("fat_loss", "endurance"):
        return 2 if level == "beginner" else 3
    return 3


def _select_exercises(filtered: List[Dict], goal: str, count: int) -> List[Dict]:
    prefer = {
        "fat_loss": ["cardio", "fullbody", "legs", "core"],
        "strength": ["chest", "back", "legs", "shoulders", "arms"],
        "fullbody": ["chest", "back", "legs", "shoulders", "core", "arms"],
        "endurance": ["cardio", "fullbody", "legs", "core"],
    }
    preferred_groups = prefer.get(goal, ["fullbody"])
    selected = []
    pool = list(filtered)

    for group in preferred_groups:
        if len(selected) >= count:
            break
        candidates = [
            e for e in pool if e["muscle_group"] == group and e not in selected
        ]
        if candidates:
            selected.append(random.choice(candidates))

    while len(selected) < count:
        remaining = [e for e in pool if e not in selected]
        if not remaining:
            break
        selected.append(random.choice(remaining))

    return selected


def generate_workout(
    available_equipment: List[str],
    goal: str,
    duration_min: int,
    level: str,
) -> Dict[str, Any]:
    filtered = filter_by_equipment(available_equipment)
    filtered = filter_by_difficulty(filtered, level)

    target_count = max(4, min(12, duration_min // 3))
    selected = _select_exercises(filtered, goal, target_count)

    rest = _get_rest_seconds(level)
    sets = _get_sets(level, goal)

    workout_exercises = []
    for ex in selected:
        item = {
            "exercise": ex,
            "sets": sets,
            "rest_seconds": rest,
        }
        if ex.get("is_timed"):
            item["duration"] = ex.get("default_duration", 40)
            item["reps"] = None
        else:
            reps = ex.get("default_reps", 12)
            if goal == "strength":
                reps = max(6, int(reps * 0.7))
            elif goal in ("endurance", "fat_loss"):
                reps = int(reps * 1.2)
            item["reps"] = reps
            item["duration"] = None
        workout_exercises.append(item)

    avg_cal = (
        sum(e.get("calories_per_min", 7) for e in selected) / max(1, len(selected))
    )
    estimated_calories = int(avg_cal * duration_min * 0.85)

    return {
        "id": f"w-{int(datetime.now().timestamp())}",
        "goal": goal,
        "duration": duration_min,
        "level": level,
        "exercises": workout_exercises,
        "estimated_calories": estimated_calories,
        "created_at": datetime.now().isoformat(),
    }


def make_session(
    workout: Dict,
    duration_minutes: int,
    exercises_completed: int,
) -> Dict:
    return {
        "id": f"s-{int(datetime.now().timestamp())}",
        "date": datetime.now().isoformat(),
        "duration_minutes": max(1, duration_minutes),
        "goal": workout["goal"],
        "level": workout["level"],
        "exercises_completed": exercises_completed,
        "total_exercises": len(workout["exercises"]),
        "estimated_calories": workout["estimated_calories"],
        "workout_name": f"{GOAL_LABELS[workout['goal']]} {workout['duration']} min",
    }
