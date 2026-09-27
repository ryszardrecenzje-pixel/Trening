"""Sygnały dźwiękowe stopera (beep przez HTML audio + base64 WAV)."""

from __future__ import annotations

import struct
import base64
import streamlit as st


def _make_beep_wav(frequency: float = 880.0, duration: float = 0.25, volume: float = 0.35) -> bytes:
    """Generuje prosty beep WAV (mono, 16-bit, 22.05 kHz)."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    frames = []
    for i in range(n_samples):
        # wygaszanie na końcu, żeby nie trzaskało
        env = 1.0
        if i > n_samples * 0.7:
            env = max(0.0, 1.0 - (i - n_samples * 0.7) / (n_samples * 0.3))
        import math
        val = int(volume * env * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        frames.append(struct.pack("<h", val))
    data = b"".join(frames)
    # nagłówek WAV
    byte_rate = sample_rate * 2
    block_align = 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        block_align,
        16,
        b"data",
        len(data),
    )
    return header + data


_BEEP_HIGH = base64.b64encode(_make_beep_wav(1046, 0.18, 0.4)).decode("ascii")
_BEEP_LOW = base64.b64encode(_make_beep_wav(660, 0.3, 0.4)).decode("ascii")
_BEEP_READY = base64.b64encode(_make_beep_wav(523, 0.12, 0.3)).decode("ascii")


def play_sound(kind: str = "tick") -> None:
    """
    kind: 'tick' (3-2-1), 'start' (start czasu), 'done' (koniec).
    Działa tylko gdy przeglądarka pozwala na autoplay po interakcji użytkownika.
    """
    if not st.session_state.get("settings", {}).get("sound_enabled", True):
        return
    b64 = {"tick": _BEEP_READY, "start": _BEEP_HIGH, "done": _BEEP_LOW}.get(kind, _BEEP_HIGH)
    # unikalny key żeby Streamlit odświeżył element
    st.markdown(
        f"""
        <audio autoplay="true" style="display:none">
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True,
    )
