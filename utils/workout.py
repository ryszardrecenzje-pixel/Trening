"""Logika generowania treningu, rozgrzewki i filtrowania ćwiczeń."""

import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from data.exercises import (
    EXERCISES,
    DIFFICULTY_LABELS,
    GOAL_LABELS,
)


# Ćwiczenia typowe na rozgrzewkę (id z bazy)
WARMUP_IDS = ["jumping_jack", "high_knees", "squat", "lunge", "plank", "mountain_climber", "inchworm", "glute_bridge", "bird_dog", "calf_raise"]


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


def get_exercise_by_id(ex_id: str) -> Optional[Dict]:
    for ex in EXERCISES:
        if ex["id"] == ex_id:
            return ex
    return None


def find_alternative(exercise: Dict, available: List[str]) -> Optional[Dict]:
    """
    Szuka zamiennika: to samo muscle_group, inny id, dostępny sprzęt.
    Preferuje pole alternative_id jeśli jest w bazie.
    """
    alt_id = exercise.get("alternative_id")
    if alt_id:
        alt = get_exercise_by_id(alt_id)
        if alt and all(eq in available for eq in alt["equipment"]):
            return alt

    candidates = [
        e
        for e in EXERCISES
        if e["id"] != exercise["id"]
        and e["muscle_group"] == exercise["muscle_group"]
        and all(eq in available for eq in e["equipment"])
    ]
    if not candidates:
        # dowolne z dostępnego sprzętu
        candidates = [
            e
            for e in EXERCISES
            if e["id"] != exercise["id"]
            and all(eq in available for eq in e["equipment"])
        ]
    return random.choice(candidates) if candidates else None


def _get_rest_seconds(level: str) -> int:
    return {"beginner": 60, "intermediate": 45, "advanced": 30}[level]


def _get_sets(level: str, goal: str) -> int:
    if goal == "strength":
        return 3 if level == "beginner" else 4
    if goal in ("fat_loss", "endurance"):
        return 2 if level == "beginner" else 3
    return 3


def _select_exercises(filtered: List[Dict], goal: str, count: int) -> List[Dict]:
    """Dobiera ćwiczenia z rotacją partii – unika powtórzeń tej samej grupy z rzędu."""
    prefer = {
        "fat_loss": ["cardio", "fullbody", "legs", "core", "chest", "back"],
        "strength": ["chest", "back", "legs", "shoulders", "arms", "core"],
        "fullbody": ["chest", "back", "legs", "shoulders", "core", "arms", "fullbody"],
        "endurance": ["cardio", "fullbody", "legs", "core", "shoulders"],
    }
    preferred_groups = prefer.get(goal, ["fullbody"])
    pool = list(filtered)
    random.shuffle(pool)
    selected: List[Dict] = []
    used_ids = set()

    # 1) Po jednym z każdej preferowanej grupy (jeśli dostępne)
    for group in preferred_groups:
        if len(selected) >= count:
            break
        candidates = [
            e for e in pool
            if e["muscle_group"] == group and e["id"] not in used_ids
        ]
        if candidates:
            choice = random.choice(candidates)
            selected.append(choice)
            used_ids.add(choice["id"])

    # 2) Uzupełnij do count – preferuj inną partię niż ostatnia
    while len(selected) < count:
        remaining = [e for e in pool if e["id"] not in used_ids]
        if not remaining:
            break
        last_group = selected[-1]["muscle_group"] if selected else None
        different = [e for e in remaining if e["muscle_group"] != last_group]
        candidates = different if different else remaining
        # lekka preferencja grup z preferred
        preferred_left = [e for e in candidates if e["muscle_group"] in preferred_groups]
        if preferred_left:
            candidates = preferred_left
        choice = random.choice(candidates)
        selected.append(choice)
        used_ids.add(choice["id"])

    # 3) Przestaw kolejność tak, by sąsiednie miały różne partie (gdy możliwe)
    if len(selected) > 2:
        improved = [selected[0]]
        rest = selected[1:]
        while rest:
            last_g = improved[-1]["muscle_group"]
            pick_i = next(
                (i for i, e in enumerate(rest) if e["muscle_group"] != last_g),
                0,
            )
            improved.append(rest.pop(pick_i))
        selected = improved

    return selected


def _build_warmup(available: List[str]) -> List[Dict]:
    """2–3 lekkie ćwiczenia na rozgrzewkę (1 seria, krótszy czas/reps)."""
    pool = filter_by_equipment(available)
    warmup_pool = [e for e in pool if e["id"] in WARMUP_IDS]
    if len(warmup_pool) < 2:
        warmup_pool = [e for e in pool if e["difficulty"] == "beginner"]
    random.shuffle(warmup_pool)
    chosen = warmup_pool[:3]
    items = []
    for ex in chosen:
        item = {
            "exercise": ex,
            "sets": 1,
            "rest_seconds": 20,
            "is_warmup": True,
        }
        if ex.get("is_timed"):
            item["duration"] = min(30, ex.get("default_duration", 30))
            item["reps"] = None
        else:
            item["reps"] = min(10, ex.get("default_reps", 10))
            item["duration"] = None
        items.append(item)
    return items


def generate_workout(
    available_equipment: List[str],
    goal: str,
    duration_min: int,
    level: str,
    include_warmup: bool = False,
) -> Dict[str, Any]:
    filtered = filter_by_equipment(available_equipment)
    filtered = filter_by_difficulty(filtered, level)

    target_count = max(4, min(12, duration_min // 3))
    selected = _select_exercises(filtered, goal, target_count)

    rest = _get_rest_seconds(level)
    sets = _get_sets(level, goal)

    workout_exercises: List[Dict] = []

    if include_warmup:
        workout_exercises.extend(_build_warmup(available_equipment))

    for ex in selected:
        item = {
            "exercise": ex,
            "sets": sets,
            "rest_seconds": rest,
            "is_warmup": False,
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

    main_ex = [e for e in workout_exercises if not e.get("is_warmup")]
    avg_cal = (
        sum(e["exercise"].get("calories_per_min", 7) for e in main_ex)
        / max(1, len(main_ex))
    )
    estimated_calories = int(avg_cal * duration_min * 0.85)

    return {
        "id": f"w-{int(datetime.now().timestamp())}",
        "goal": goal,
        "duration": duration_min,
        "level": level,
        "include_warmup": include_warmup,
        "exercises": workout_exercises,
        "estimated_calories": estimated_calories,
        "created_at": datetime.now().isoformat(),
    }


def make_session(
    workout: Dict,
    duration_minutes: int,
    exercises_completed: int,
    rpe: Optional[int] = None,
    note: str = "",
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
        "rpe": rpe,
        "note": note or "",
    }
