"""
Home Workout – Trening w domu
Aplikacja Streamlit z dynamicznym dostosowywaniem planów do sprzętu użytkownika.
"""

import sys
from pathlib import Path

# Zapewnia poprawne importy na Streamlit Cloud (ścieżka /mount/src/...)
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
from datetime import datetime

import streamlit as st

from data.exercises import (
    ALL_EQUIPMENT,
    EQUIPMENT_LABELS,
    GOAL_LABELS,
    DIFFICULTY_LABELS,
    MUSCLE_GROUP_LABELS,
)
from utils.workout import generate_workout, make_session

# ──────────────────────────────────────────────
# Konfiguracja strony
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Home Workout 🏋️",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# Inicjalizacja stanu
# ──────────────────────────────────────────────
def init_state():
    defaults = {
        "equipment": ["bodyweight"],
        "history": [],
        "page": "trening",          # trening | sprzet | historia | player
        "generated_workout": None,
        "player_idx": 0,            # indeks ćwiczenia
        "player_set": 1,            # aktualna seria
        "player_phase": "exercise", # exercise | rest | complete
        "player_start_ts": None,
        "completed_exercises": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# ──────────────────────────────────────────────
# Style CSS (mobile-first, dark, sportowy)
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
    /* Ukryj domyślne elementy Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 6rem;
        max-width: 480px;
    }
    
    /* Karty */
    .card {
        background: #1a1a25;
        border: 1px solid #2a2a3a;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .card-selected {
        background: rgba(34, 197, 94, 0.15);
        border-color: #22c55e;
    }
    
    /* Duże przyciski */
    .stButton > button {
        width: 100%;
        border-radius: 14px;
        font-weight: 600;
        padding: 0.7rem 1rem;
        font-size: 1rem;
    }
    
    /* Progress */
    .progress-bar {
        height: 6px;
        background: #1a1a25;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0 1rem;
    }
    .progress-fill {
        height: 100%;
        background: #22c55e;
        border-radius: 4px;
        transition: width 0.3s;
    }
    
    /* Timer */
    .timer-display {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        color: #22c55e;
        font-variant-numeric: tabular-nums;
        margin: 1rem 0;
    }
    .timer-rest {
        color: #f97316;
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
    }
    
    /* Stat boxes */
    .stat-box {
        background: #1a1a25;
        border: 1px solid #2a2a3a;
        border-radius: 14px;
        padding: 0.8rem;
        text-align: center;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f4f4f5;
    }
    .stat-label {
        font-size: 0.7rem;
        color: #71717a;
    }
    
    /* Bottom nav */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(18, 18, 26, 0.95);
        border-top: 1px solid #2a2a3a;
        display: flex;
        justify-content: space-around;
        padding: 0.5rem 0;
        z-index: 100;
        backdrop-filter: blur(8px);
    }
    .nav-btn {
        text-align: center;
        color: #71717a;
        font-size: 0.7rem;
        padding: 0.3rem 1rem;
        cursor: pointer;
        text-decoration: none;
    }
    .nav-btn.active {
        color: #22c55e;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Nawigacja dolna (symulowana przyciskami)
# ──────────────────────────────────────────────
def render_nav():
    if st.session_state.page == "player":
        return  # pełny ekran gracza

    cols = st.columns(3)
    labels = [("🏋️ Trening", "trening"), ("🛠️ Sprzęt", "sprzet"), ("📜 Historia", "historia")]
    for col, (label, key) in zip(cols, labels):
        with col:
            is_active = st.session_state.page == key
            if st.button(
                label,
                key=f"nav_{key}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = key
                st.rerun()


# ──────────────────────────────────────────────
# STRONA: SPRZĘT
# ──────────────────────────────────────────────
def page_equipment():
    st.title("🛠️ Twój sprzęt")
    st.caption("Zaznacz posiadany sprzęt – plany dostosują się automatycznie.")

    st.info("**Masa własnego ciała** jest zawsze dostępna. Im więcej sprzętu, tym bogatsze treningi.")

    current = st.session_state.equipment

    for eq in ALL_EQUIPMENT:
        label = EQUIPMENT_LABELS[eq]
        is_body = eq == "bodyweight"
        checked = eq in current

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{label}**" + (" _(zawsze)_" if is_body else ""))
        with col2:
            if is_body:
                st.checkbox("", value=True, disabled=True, key=f"eq_{eq}")
            else:
                new_val = st.checkbox("", value=checked, key=f"eq_{eq}")
                if new_val and eq not in current:
                    st.session_state.equipment = current + [eq]
                    st.rerun()
                elif not new_val and eq in current:
                    st.session_state.equipment = [e for e in current if e != eq]
                    st.rerun()

    st.success(f"Zaznaczono: **{len(st.session_state.equipment)}** pozycji sprzętu")


# ──────────────────────────────────────────────
# STRONA: GENERATOR TRENINGU
# ──────────────────────────────────────────────
def page_workout():
    st.title("🏋️ Generator treningu")
    st.caption(
        f"Dostosowany do Twojego sprzętu ({len(st.session_state.equipment)} pozycji)"
    )

    # Cel
    st.subheader("Cel treningu")
    goal_options = list(GOAL_LABELS.keys())
    goal = st.radio(
        "Cel",
        goal_options,
        format_func=lambda x: GOAL_LABELS[x],
        horizontal=True,
        label_visibility="collapsed",
        key="goal_select",
    )

    # Czas
    st.subheader("Czas trwania")
    duration = st.radio(
        "Czas",
        [15, 30, 45],
        format_func=lambda x: f"{x} min",
        horizontal=True,
        label_visibility="collapsed",
        key="duration_select",
        index=1,
    )

    # Poziom
    st.subheader("Poziom")
    level = st.radio(
        "Poziom",
        ["beginner", "intermediate", "advanced"],
        format_func=lambda x: DIFFICULTY_LABELS[x],
        horizontal=True,
        label_visibility="collapsed",
        key="level_select",
        index=1,
    )

    st.divider()

    if st.button("⚡ Generuj trening", type="primary", use_container_width=True):
        workout = generate_workout(
            st.session_state.equipment, goal, duration, level
        )
        st.session_state.generated_workout = workout
        st.rerun()

    # Podgląd
    workout = st.session_state.generated_workout
    if workout:
        st.markdown("---")
        st.markdown(
            f"### {GOAL_LABELS[workout['goal']]} • {workout['duration']} min"
        )
        st.caption(
            f"{len(workout['exercises'])} ćwiczeń • ~{workout['estimated_calories']} kcal • "
            f"{DIFFICULTY_LABELS[workout['level']]}"
        )

        for i, we in enumerate(workout["exercises"], 1):
            ex = we["exercise"]
            detail = (
                f"{we['sets']} × {we['duration']}s"
                if we.get("duration")
                else f"{we['sets']} × {we['reps']} powt."
            )
            st.markdown(
                f"""
                <div class="card">
                    <strong>{i}. {ex['name_pl']}</strong><br>
                    <span style="color:#71717a;font-size:0.85rem">
                        {MUSCLE_GROUP_LABELS[ex['muscle_group']]} • {detail}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button(
            "▶️ Rozpocznij trening",
            type="primary",
            use_container_width=True,
            key="start_btn",
        ):
            st.session_state.page = "player"
            st.session_state.player_idx = 0
            st.session_state.player_set = 1
            st.session_state.player_phase = "exercise"
            st.session_state.player_start_ts = time.time()
            st.session_state.completed_exercises = 0
            st.rerun()


# ──────────────────────────────────────────────
# STRONA: GRACZ TRENINGU (bez blokujących sleep)
# ──────────────────────────────────────────────
def page_player():
    workout = st.session_state.generated_workout
    if not workout:
        st.session_state.page = "trening"
        st.rerun()
        return

    exercises = workout["exercises"]
    idx = st.session_state.player_idx
    current_set = st.session_state.player_set
    phase = st.session_state.player_phase

    # ── Zakończony trening ──
    if phase == "complete":
        elapsed = int((time.time() - st.session_state.player_start_ts) / 60)
        st.balloons()
        st.title("🎉 Brawo!")
        st.subheader("Trening ukończony")

        c1, c2 = st.columns(2)
        c1.metric("Czas", f"{max(1, elapsed)} min")
        c2.metric("Kalorie", f"~{workout['estimated_calories']} kcal")

        if st.button("💾 Zapisz i wróć", type="primary", use_container_width=True):
            session = make_session(
                workout,
                max(1, elapsed),
                st.session_state.completed_exercises or len(exercises),
            )
            st.session_state.history.insert(0, session)
            st.session_state.history = st.session_state.history[:50]
            st.session_state.page = "historia"
            st.session_state.generated_workout = None
            st.rerun()
        return

    # ── Aktualne ćwiczenie ──
    we = exercises[idx]
    ex = we["exercise"]
    total_sets_all = sum(e["sets"] for e in exercises)
    done_sets = sum(e["sets"] for e in exercises[:idx]) + (current_set - 1)
    progress_pct = int((done_sets / max(1, total_sets_all)) * 100)

    # Nagłówek
    col_x, col_info = st.columns([1, 5])
    with col_x:
        if st.button("❌", key="cancel_workout"):
            st.session_state.page = "trening"
            st.session_state.generated_workout = None
            st.rerun()
    with col_info:
        st.caption(
            f"Ćwiczenie {idx + 1}/{len(exercises)}  •  Seria {current_set}/{we['sets']}"
        )

    # Progress bar
    st.markdown(
        f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width:{progress_pct}%"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if phase == "exercise":
        st.markdown(
            f"<p style='text-align:center;color:#22c55e;font-size:0.8rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:1px'>"
            f"{MUSCLE_GROUP_LABELS[ex['muscle_group']]}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h2 style='text-align:center;margin:0.2rem 0'>{ex['name_pl']}</h2>",
            unsafe_allow_html=True,
        )

        if we.get("duration"):
            # Ćwiczenie czasowe – pokaż cel i przycisk
            mins, secs = divmod(we["duration"], 60)
            st.markdown(
                f"<div class='timer-display'>{mins:02d}:{secs:02d}</div>",
                unsafe_allow_html=True,
            )
            st.caption("Wykonuj ćwiczenie przez powyższy czas, potem kliknij Zrobione.")
        else:
            st.markdown(
                f"<div class='timer-display'>{we['reps']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align:center;color:#71717a'>powtórzeń</p>",
                unsafe_allow_html=True,
            )

        st.info(ex["instructions_pl"])

        if st.button(
            "✅ Zrobione – następna",
            type="primary",
            use_container_width=True,
            key="done_btn",
        ):
            _advance_after_exercise()

    elif phase == "rest":
        rest_sec = we["rest_seconds"]
        mins, secs = divmod(rest_sec, 60)

        st.markdown(
            "<p style='text-align:center;color:#71717a;font-size:1.1rem'>⏱️ Przerwa</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='timer-display timer-rest'>{mins:02d}:{secs:02d}</div>",
            unsafe_allow_html=True,
        )

        # Co będzie dalej
        is_last_set = current_set >= we["sets"]
        is_last_ex = idx >= len(exercises) - 1
        if is_last_set and not is_last_ex:
            next_name = exercises[idx + 1]["exercise"]["name_pl"]
        elif not is_last_set:
            next_name = f"{ex['name_pl']} (seria {current_set + 1})"
        else:
            next_name = "Koniec treningu"

        st.caption(f"Następne: **{next_name}**")
        st.caption(f"Odpocznij ok. {rest_sec} sekund, potem kontynuuj.")

        if st.button(
            "▶️ Koniec przerwy – dalej",
            type="primary",
            use_container_width=True,
            key="end_rest_btn",
        ):
            _advance_after_rest()


def _advance_after_exercise():
    """Po ukończeniu serii ćwiczenia → przerwa lub koniec."""
    workout = st.session_state.generated_workout
    exercises = workout["exercises"]
    idx = st.session_state.player_idx
    current_set = st.session_state.player_set
    we = exercises[idx]

    is_last_set = current_set >= we["sets"]
    is_last_ex = idx >= len(exercises) - 1

    if is_last_set and is_last_ex:
        st.session_state.player_phase = "complete"
        st.session_state.completed_exercises = len(exercises)
    else:
        st.session_state.player_phase = "rest"
    st.rerun()


def _advance_after_rest():
    """Po przerwie → następna seria lub następne ćwiczenie."""
    workout = st.session_state.generated_workout
    exercises = workout["exercises"]
    idx = st.session_state.player_idx
    current_set = st.session_state.player_set
    we = exercises[idx]

    is_last_set = current_set >= we["sets"]
    is_last_ex = idx >= len(exercises) - 1

    if is_last_set:
        if is_last_ex:
            st.session_state.player_phase = "complete"
            st.session_state.completed_exercises = len(exercises)
        else:
            st.session_state.player_idx = idx + 1
            st.session_state.player_set = 1
            st.session_state.player_phase = "exercise"
            st.session_state.completed_exercises += 1
    else:
        st.session_state.player_set = current_set + 1
        st.session_state.player_phase = "exercise"

    st.rerun()


# ──────────────────────────────────────────────
# STRONA: HISTORIA
# ──────────────────────────────────────────────
def page_history():
    st.title("📜 Historia")
    st.caption("Twoje ukończone treningi")

    history = st.session_state.history

    # Statystyki
    total_sessions = len(history)
    total_minutes = sum(h["duration_minutes"] for h in history)
    total_calories = sum(h["estimated_calories"] for h in history)

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="stat-box"><div class="stat-value">{total_sessions}</div>'
        f'<div class="stat-label">treningów</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="stat-box"><div class="stat-value">{total_minutes}</div>'
        f'<div class="stat-label">minut</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="stat-box"><div class="stat-value">{total_calories}</div>'
        f'<div class="stat-label">kcal</div></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    if not history:
        st.info("Brak historii. Ukończ pierwszy trening, aby zobaczyć go tutaj.")
        return

    if st.button("🗑️ Wyczyść historię", type="secondary"):
        st.session_state.history = []
        st.rerun()

    for session in history:
        dt = datetime.fromisoformat(session["date"])
        date_str = dt.strftime("%d %b %Y, %H:%M")
        st.markdown(
            f"""
            <div class="card">
                <strong>{session['workout_name']}</strong>
                <span class="badge" style="float:right">{DIFFICULTY_LABELS[session['level']]}</span>
                <br>
                <span style="color:#71717a;font-size:0.8rem">{date_str}</span>
                <br>
                <span style="font-size:0.85rem;margin-top:0.4rem;display:inline-block">
                    <strong>{session['duration_minutes']}</strong> min &nbsp;·&nbsp;
                    <strong>{session['exercises_completed']}/{session['total_exercises']}</strong> ćw. &nbsp;·&nbsp;
                    <strong style="color:#f97316">~{session['estimated_calories']}</strong> kcal
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────
# GŁÓWNY ROUTER
# ──────────────────────────────────────────────
page = st.session_state.page

if page == "player":
    page_player()
elif page == "sprzet":
    page_equipment()
    render_nav()
elif page == "historia":
    page_history()
    render_nav()
else:
    page_workout()
    render_nav()
