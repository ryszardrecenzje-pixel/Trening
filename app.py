"""
Home Workout – Trening w domu
Streamlit: generator planów, stoper, GIF-y, historia, ulubione, statystyki.
"""

from __future__ import annotations

import sys
import math
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from data.exercises import (
    ALL_EQUIPMENT,
    EQUIPMENT_LABELS,
    GOAL_LABELS,
    DIFFICULTY_LABELS,
    MUSCLE_GROUP_LABELS,
)
from utils.workout import generate_workout, make_session, find_alternative
from utils.storage import (
    load_history,
    save_history,
    add_history_entry,
    load_favorites,
    save_favorites,
    add_favorite,
    remove_favorite,
    load_settings,
    save_settings,
    compute_stats,
    export_all,
    import_all,
)
from utils.i18n import t
from utils.audio import play_sound

st.set_page_config(
    page_title="Home Workout 🏋️",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def init_state():
    if "hydrated" not in st.session_state:
        settings = load_settings()
        st.session_state.settings = settings
        st.session_state.history = load_history()
        st.session_state.favorites = load_favorites()
        st.session_state.hydrated = True

    defaults = {
        "equipment": ["bodyweight"],
        "page": "trening",
        "generated_workout": None,
        "player_idx": 0,
        "player_set": 1,
        "player_phase": "exercise",
        "player_start_ts": None,
        "completed_exercises": 0,
        "timer_mode": "idle",
        "timer_total": 0,
        "timer_remaining": 0,
        "timer_deadline": None,
        "timer_ready_deadline": None,
        "timer_context": None,
        "last_ready_beep": None,
        "rpe_value": 5,
        "session_note": "",
        "show_onboarding": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.show_onboarding is None:
        st.session_state.show_onboarding = not st.session_state.settings.get(
            "onboarding_done", False
        )


init_state()
LANG = st.session_state.settings.get("language", "pl")

st.markdown(
    """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 7rem;
        max-width: 480px;
    }
    .card {
        background: #1a1a25;
        border: 1px solid #2a2a3a;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 14px;
        font-weight: 600;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        min-height: 48px;
    }
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
    .timer-display {
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        color: #22c55e;
        font-variant-numeric: tabular-nums;
        margin: 0.6rem 0;
    }
    .timer-rest { color: #f97316; }
    .badge {
        display: inline-block;
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
    }
    .stat-box {
        background: #1a1a25;
        border: 1px solid #2a2a3a;
        border-radius: 14px;
        padding: 0.8rem;
        text-align: center;
    }
    .stat-value { font-size: 1.4rem; font-weight: 700; color: #f4f4f5; }
    .stat-label { font-size: 0.7rem; color: #71717a; }
    .warmup-tag {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
    }
    img { border-radius: 12px; }
</style>
""",
    unsafe_allow_html=True,
)


def _reset_timer(seconds, context):
    st.session_state.timer_mode = "idle"
    st.session_state.timer_total = seconds or 0
    st.session_state.timer_remaining = seconds or 0
    st.session_state.timer_deadline = None
    st.session_state.timer_ready_deadline = None
    st.session_state.timer_context = context
    st.session_state.last_ready_beep = None


def _start_timer():
    st.session_state.timer_mode = "get_ready"
    st.session_state.timer_ready_deadline = time.time() + 3
    st.session_state.last_ready_beep = None


def _stop_timer():
    if st.session_state.timer_mode == "running" and st.session_state.timer_deadline:
        left = max(0, int(round(st.session_state.timer_deadline - time.time())))
        st.session_state.timer_remaining = left
    st.session_state.timer_mode = "paused"
    st.session_state.timer_deadline = None
    st.session_state.timer_ready_deadline = None


def _format_mmss(seconds: int) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m:02d}:{s:02d}"


def _render_timer_controls(css_class: str = "timer-display") -> bool:
    mode = st.session_state.timer_mode
    remaining = st.session_state.timer_remaining

    if mode == "get_ready" and st.session_state.timer_ready_deadline:
        left_ready = st.session_state.timer_ready_deadline - time.time()
        if left_ready <= 0:
            st.session_state.timer_mode = "running"
            st.session_state.timer_deadline = (
                time.time() + st.session_state.timer_remaining
            )
            st.session_state.timer_ready_deadline = None
            play_sound("start")
            st.rerun()
        else:
            n = max(1, int(math.ceil(left_ready)))
            if st.session_state.last_ready_beep != n:
                st.session_state.last_ready_beep = n
                play_sound("tick")
            st.markdown(
                f"<div class='{css_class}' style='color:#fbbf24;font-size:4rem'>{n}</div>",
                unsafe_allow_html=True,
            )
            st.caption(t("get_ready", LANG))
            time.sleep(0.15)
            st.rerun()

    if mode == "running" and st.session_state.timer_deadline:
        left = st.session_state.timer_deadline - time.time()
        if left <= 0:
            st.session_state.timer_remaining = 0
            st.session_state.timer_mode = "finished"
            st.session_state.timer_deadline = None
            play_sound("done")
            st.rerun()
        else:
            remaining = max(0, int(math.ceil(left)))
            st.session_state.timer_remaining = remaining

    if mode == "finished":
        st.markdown(f"<div class='{css_class}'>00:00</div>", unsafe_allow_html=True)
        st.success(t("time_up", LANG))
        return True

    if mode != "get_ready":
        st.markdown(
            f"<div class='{css_class}'>{_format_mmss(remaining)}</div>",
            unsafe_allow_html=True,
        )

    if mode in ("idle", "paused"):
        label = t("start", LANG) if mode == "idle" else t("resume", LANG)
        if st.button(label, type="primary", use_container_width=True, key="timer_start"):
            _start_timer()
            st.rerun()
    elif mode == "running":
        if st.button(t("stop", LANG), type="secondary", use_container_width=True, key="timer_stop"):
            _stop_timer()
            st.rerun()
        time.sleep(0.2)
        st.rerun()

    return False


def render_nav():
    if st.session_state.page == "player":
        return
    cols = st.columns(4)
    items = [
        (t("nav_workout", LANG), "trening"),
        (t("nav_equipment", LANG), "sprzet"),
        (t("nav_history", LANG), "historia"),
        (t("nav_more", LANG), "wiecej"),
    ]
    for col, (label, key) in zip(cols, items):
        with col:
            active = st.session_state.page == key
            if st.button(
                label,
                key=f"nav_{key}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = key
                st.rerun()


def render_onboarding():
    if not st.session_state.show_onboarding:
        return
    st.info(f"**{t('onboarding_title', LANG)}**")
    st.markdown(t("onboarding_1", LANG))
    st.markdown(t("onboarding_2", LANG))
    st.markdown(t("onboarding_3", LANG))
    if st.button(t("got_it", LANG), type="primary", use_container_width=True):
        st.session_state.show_onboarding = False
        st.session_state.settings["onboarding_done"] = True
        save_settings(st.session_state.settings)
        st.rerun()
    st.divider()


def page_equipment():
    st.title(t("equipment_title", LANG))
    st.caption(t("equipment_hint", LANG))
    st.info(t("equipment_body_always", LANG))
    current = list(st.session_state.equipment)
    for eq in ALL_EQUIPMENT:
        label = EQUIPMENT_LABELS[eq]
        is_body = eq == "bodyweight"
        checked = eq in current
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"**{label}**" + (" _(✓)_" if is_body else ""))
        with c2:
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
    st.success(f"**{len(st.session_state.equipment)}**")


def page_workout():
    render_onboarding()
    st.title(t("generator_title", LANG))
    st.caption(f"({len(st.session_state.equipment)})")

    favs = st.session_state.favorites
    if favs:
        with st.expander(f"⭐ {t('favorites', LANG)} ({len(favs)})", expanded=False):
            for fav in favs:
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(
                        f"{fav.get('name', 'Plan')}",
                        key=f"fav_load_{fav.get('name')}",
                        use_container_width=True,
                    ):
                        w = generate_workout(
                            st.session_state.equipment,
                            fav["goal"],
                            fav["duration"],
                            fav["level"],
                            include_warmup=fav.get("include_warmup", False),
                        )
                        st.session_state.generated_workout = w
                        st.rerun()
                with c2:
                    if st.button("🗑️", key=f"fav_del_{fav.get('name')}"):
                        st.session_state.favorites = remove_favorite(
                            favs, fav.get("name", "")
                        )
                        st.rerun()

    st.subheader(t("goal", LANG))
    goal = st.radio(
        "g",
        list(GOAL_LABELS.keys()),
        format_func=lambda x: GOAL_LABELS[x],
        horizontal=True,
        label_visibility="collapsed",
        key="goal_select",
    )

    st.subheader(t("duration", LANG))
    duration = st.radio(
        "d",
        [15, 30, 45],
        format_func=lambda x: f"{x} min",
        horizontal=True,
        label_visibility="collapsed",
        key="duration_select",
        index=1,
    )

    st.subheader(t("level", LANG))
    level = st.radio(
        "l",
        ["beginner", "intermediate", "advanced"],
        format_func=lambda x: DIFFICULTY_LABELS[x],
        horizontal=True,
        label_visibility="collapsed",
        key="level_select",
        index=1,
    )

    include_warmup = st.toggle(t("warmup", LANG), value=True, key="warmup_toggle")
    st.divider()

    if st.button(t("generate", LANG), type="primary", use_container_width=True):
        with st.spinner("…"):
            workout = generate_workout(
                st.session_state.equipment,
                goal,
                duration,
                level,
                include_warmup=include_warmup,
            )
        st.session_state.generated_workout = workout
        st.rerun()

    workout = st.session_state.generated_workout
    if not workout:
        return

    st.markdown("---")
    st.markdown(f"### {GOAL_LABELS[workout['goal']]} • {workout['duration']} min")
    n_main = sum(1 for e in workout["exercises"] if not e.get("is_warmup"))
    n_wu = sum(1 for e in workout["exercises"] if e.get("is_warmup"))
    extra = f" + {n_wu} WU" if n_wu else ""
    st.caption(
        f"{n_main} ćw.{extra} • ~{workout['estimated_calories']} kcal • "
        f"{DIFFICULTY_LABELS[workout['level']]}"
    )

    for i, we in enumerate(workout["exercises"], 1):
        ex = we["exercise"]
        detail = (
            f"{we['sets']} × {we['duration']}s"
            if we.get("duration")
            else f"{we['sets']} × {we['reps']} {t('reps', LANG)}"
        )
        tag = ' <span class="warmup-tag">WU</span>' if we.get("is_warmup") else ""
        st.markdown(
            f'<div class="card"><strong>{i}. {ex["name_pl"]}</strong>{tag}<br>'
            f'<span style="color:#71717a;font-size:0.85rem">'
            f'{MUSCLE_GROUP_LABELS[ex["muscle_group"]]} • {detail}</span></div>',
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("start_workout", LANG),
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
            first = workout["exercises"][0]
            if first.get("duration"):
                _reset_timer(first["duration"], "exercise")
            else:
                _reset_timer(0, "exercise")
            st.rerun()
    with c2:
        if st.button(t("save_favorite", LANG), use_container_width=True, key="save_fav"):
            name = f"{GOAL_LABELS[workout['goal']]} {workout['duration']}min"
            fav = {
                "name": name,
                "goal": workout["goal"],
                "duration": workout["duration"],
                "level": workout["level"],
                "include_warmup": workout.get("include_warmup", False),
            }
            st.session_state.favorites = add_favorite(st.session_state.favorites, fav)
            st.success("⭐")
            st.rerun()


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

    if phase == "complete":
        elapsed = int((time.time() - st.session_state.player_start_ts) / 60)
        st.balloons()
        st.title(t("bravo", LANG))
        st.subheader(t("workout_complete", LANG))
        c1, c2 = st.columns(2)
        c1.metric("min", f"{max(1, elapsed)}")
        c2.metric("kcal", f"~{workout['estimated_calories']}")

        st.subheader(t("rpe_label", LANG))
        rpe = st.slider("RPE", 1, 10, 5, key="rpe_slider")
        note = st.text_input(t("note_label", LANG), key="note_input")

        if st.button(t("save_return", LANG), type="primary", use_container_width=True):
            session = make_session(
                workout,
                max(1, elapsed),
                st.session_state.completed_exercises or len(exercises),
                rpe=rpe,
                note=note,
            )
            st.session_state.history = add_history_entry(
                st.session_state.history, session
            )
            st.session_state.page = "historia"
            st.session_state.generated_workout = None
            st.rerun()
        return

    we = exercises[idx]
    ex = we["exercise"]
    total_sets_all = sum(e["sets"] for e in exercises)
    done_sets = sum(e["sets"] for e in exercises[:idx]) + (current_set - 1)
    progress_pct = int((done_sets / max(1, total_sets_all)) * 100)

    col_x, col_info = st.columns([1, 5])
    with col_x:
        if st.button("❌", key="cancel_workout"):
            st.session_state.page = "trening"
            st.session_state.generated_workout = None
            st.rerun()
    with col_info:
        wu = " · WU" if we.get("is_warmup") else ""
        st.caption(f"{idx + 1}/{len(exercises)}  •  {current_set}/{we['sets']}{wu}")

    st.markdown(
        f'<div class="progress-bar"><div class="progress-fill" style="width:{progress_pct}%"></div></div>',
        unsafe_allow_html=True,
    )

    if phase == "exercise":
        st.markdown(
            f"<p style='text-align:center;color:#22c55e;font-size:0.8rem;font-weight:600;"
            f"text-transform:uppercase'>{MUSCLE_GROUP_LABELS[ex['muscle_group']]}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h2 style='text-align:center;margin:0.2rem 0'>{ex['name_pl']}</h2>",
            unsafe_allow_html=True,
        )

        gif = ex.get("gif_url")
        if gif:
            try:
                st.image(gif, use_container_width=True, caption=t("preview_move", LANG))
            except Exception:
                st.caption("(brak podglądu)")

        if ex.get("safety_tip"):
            st.warning(f"{t('safety', LANG)}: {ex['safety_tip']}")

        alt = find_alternative(ex, st.session_state.equipment)
        if alt and alt["id"] != ex["id"]:
            st.caption(f"{t('alternative', LANG)}: **{alt['name_pl']}**")

        if we.get("duration"):
            if (
                st.session_state.timer_context != "exercise"
                or st.session_state.timer_total != we["duration"]
            ) and st.session_state.timer_mode in ("idle", "finished"):
                _reset_timer(we["duration"], "exercise")

            finished = _render_timer_controls("timer-display")
            if finished:
                if st.button(
                    "✅ Dalej", type="primary", use_container_width=True, key="timer_done_ex"
                ):
                    _advance_after_exercise()
            else:
                if st.session_state.timer_mode in ("idle", "paused"):
                    if st.button(
                        t("done", LANG), use_container_width=True, key="done_early_ex"
                    ):
                        _stop_timer()
                        _advance_after_exercise()
            st.info(ex["instructions_pl"])
        else:
            st.markdown(
                f"<div class='timer-display'>{we['reps']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='text-align:center;color:#71717a'>{t('reps', LANG)}</p>",
                unsafe_allow_html=True,
            )
            st.info(ex["instructions_pl"])
            if st.button(
                t("done", LANG), type="primary", use_container_width=True, key="done_btn"
            ):
                _advance_after_exercise()

    elif phase == "rest":
        rest_sec = we["rest_seconds"]
        st.markdown(
            f"<p style='text-align:center;color:#71717a;font-size:1.1rem'>{t('rest', LANG)}</p>",
            unsafe_allow_html=True,
        )
        is_last_set = current_set >= we["sets"]
        is_last_ex = idx >= len(exercises) - 1
        if is_last_set and not is_last_ex:
            next_name = exercises[idx + 1]["exercise"]["name_pl"]
        elif not is_last_set:
            next_name = f"{ex['name_pl']} ({current_set + 1})"
        else:
            next_name = "✓"
        st.caption(f"{t('next', LANG)}: **{next_name}**")

        if (
            st.session_state.timer_context != "rest"
            or st.session_state.timer_total != rest_sec
        ) and st.session_state.timer_mode in ("idle", "finished"):
            _reset_timer(rest_sec, "rest")

        finished = _render_timer_controls("timer-display timer-rest")
        if finished:
            if st.button(
                "▶️ Dalej", type="primary", use_container_width=True, key="timer_done_rest"
            ):
                _advance_after_rest()
        else:
            if st.button(
                t("skip_rest", LANG), use_container_width=True, key="skip_rest_btn"
            ):
                _stop_timer()
                _advance_after_rest()


def _advance_after_exercise():
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
        _reset_timer(0, None)
    else:
        st.session_state.player_phase = "rest"
        _reset_timer(we["rest_seconds"], "rest")
    st.rerun()


def _advance_after_rest():
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
            _reset_timer(0, None)
        else:
            st.session_state.player_idx = idx + 1
            st.session_state.player_set = 1
            st.session_state.player_phase = "exercise"
            st.session_state.completed_exercises += 1
            nxt = exercises[idx + 1]
            if nxt.get("duration"):
                _reset_timer(nxt["duration"], "exercise")
            else:
                _reset_timer(0, "exercise")
    else:
        st.session_state.player_set = current_set + 1
        st.session_state.player_phase = "exercise"
        if we.get("duration"):
            _reset_timer(we["duration"], "exercise")
        else:
            _reset_timer(0, "exercise")
    st.rerun()


def page_history():
    st.title(t("history_title", LANG))
    history = st.session_state.history
    stats = compute_stats(history)

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="stat-box"><div class="stat-value">{stats["streak"]}</div>'
        f'<div class="stat-label">{t("stats_streak", LANG)}</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="stat-box"><div class="stat-value">{stats["week_sessions"]}</div>'
        f'<div class="stat-label">{t("stats_week", LANG)}</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="stat-box"><div class="stat-value">{stats["total_sessions"]}</div>'
        f'<div class="stat-label">Σ</div></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"{stats['week_minutes']} min / ~{stats['week_calories']} kcal (tydzień) · "
        f"{stats['total_minutes']} min łącznie"
    )
    st.divider()

    if not history:
        st.info(t("no_history", LANG))
        if st.button(t("start_workout", LANG), type="primary", use_container_width=True):
            st.session_state.page = "trening"
            st.rerun()
        return

    if st.button(t("clear_history", LANG), type="secondary"):
        st.session_state.history = []
        save_history([])
        st.rerun()

    for session in history:
        try:
            dt = datetime.fromisoformat(session["date"])
            date_str = dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            date_str = session.get("date", "")
        rpe = session.get("rpe")
        note = session.get("note") or ""
        extra = f" · RPE {rpe}" if rpe else ""
        if note:
            extra += f"<br><em style='color:#a1a1aa'>{note}</em>"
        st.markdown(
            f'<div class="card"><strong>{session.get("workout_name", "Trening")}</strong>'
            f'<span class="badge" style="float:right">'
            f'{DIFFICULTY_LABELS.get(session.get("level", ""), "")}</span><br>'
            f'<span style="color:#71717a;font-size:0.8rem">{date_str}</span><br>'
            f'<span style="font-size:0.85rem"><strong>{session.get("duration_minutes", 0)}</strong> min · '
            f'<strong>{session.get("exercises_completed", 0)}/{session.get("total_exercises", 0)}</strong> · '
            f'<strong style="color:#f97316">~{session.get("estimated_calories", 0)}</strong> kcal{extra}</span></div>',
            unsafe_allow_html=True,
        )


def page_more():
    st.title(t("nav_more", LANG))

    st.subheader(t("language", LANG))
    lang = st.radio(
        "lang",
        ["pl", "en"],
        format_func=lambda x: "Polski" if x == "pl" else "English",
        index=0 if LANG == "pl" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="lang_radio",
    )
    if lang != st.session_state.settings.get("language"):
        st.session_state.settings["language"] = lang
        save_settings(st.session_state.settings)
        st.rerun()

    st.subheader(t("sound", LANG))
    sound = st.toggle(
        t("sound", LANG),
        value=st.session_state.settings.get("sound_enabled", True),
        key="sound_toggle",
    )
    if sound != st.session_state.settings.get("sound_enabled", True):
        st.session_state.settings["sound_enabled"] = sound
        save_settings(st.session_state.settings)

    st.divider()
    st.subheader("Backup")
    st.caption(
        "Na Streamlit Cloud pliki mogą znikać po restarcie – eksportuj kopię zapasową."
    )
    payload = export_all(
        st.session_state.history,
        st.session_state.favorites,
        st.session_state.settings,
    )
    st.download_button(
        t("export", LANG),
        data=payload,
        file_name=f"home-workout-backup-{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded = st.file_uploader(t("import", LANG), type=["json"])
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        data = import_all(raw)
        if data:
            st.session_state.history = data["history"]
            st.session_state.favorites = data["favorites"]
            st.session_state.settings = data["settings"]
            save_history(data["history"])
            save_favorites(data["favorites"])
            save_settings(data["settings"])
            st.success("OK")
            st.rerun()
        else:
            st.error("Nieprawidłowy plik")

    st.divider()
    if st.button("Pokaż ponownie wprowadzenie", use_container_width=True):
        st.session_state.show_onboarding = True
        st.session_state.page = "trening"
        st.rerun()
    st.caption("Home Workout · JSON lokalnie · Supabase później")


page = st.session_state.page
if page == "player":
    page_player()
elif page == "sprzet":
    page_equipment()
    render_nav()
elif page == "historia":
    page_history()
    render_nav()
elif page == "wiecej":
    page_more()
    render_nav()
else:
    page_workout()
    render_nav()
