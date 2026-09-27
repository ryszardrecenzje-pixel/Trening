"""Klient Supabase – konfiguracja z st.secrets lub zmiennych środowiskowych."""

from __future__ import annotations

from typing import Any, Optional

_client = None
_init_error: Optional[str] = None


def _read_config() -> tuple[Optional[str], Optional[str]]:
    url = key = None
    try:
        import streamlit as st

        if "supabase" in st.secrets:
            url = st.secrets["supabase"].get("url")
            key = st.secrets["supabase"].get("anon_key") or st.secrets["supabase"].get(
                "key"
            )
    except Exception:
        pass

    if not url or not key:
        import os

        url = url or os.environ.get("SUPABASE_URL")
        key = key or os.environ.get("SUPABASE_ANON_KEY") or os.environ.get(
            "SUPABASE_KEY"
        )

    return url, key


def is_supabase_configured() -> bool:
    url, key = _read_config()
    return bool(url and key)


def get_supabase():
    """Zwraca klienta Supabase lub None + zapisuje błąd inicjalizacji."""
    global _client, _init_error
    if _client is not None:
        return _client
    if _init_error is not None and not is_supabase_configured():
        return None

    url, key = _read_config()
    if not url or not key:
        _init_error = "Brak SUPABASE_URL / anon_key w secrets"
        return None

    try:
        from supabase import create_client

        _client = create_client(url, key)
        _init_error = None
        return _client
    except Exception as e:
        _init_error = str(e)
        _client = None
        return None


def supabase_status() -> dict[str, Any]:
    """Status połączenia do UI."""
    configured = is_supabase_configured()
    client = get_supabase() if configured else None
    ok = client is not None
    return {
        "configured": configured,
        "connected": ok,
        "error": _init_error,
        "backend": "supabase" if ok else "local_json",
    }
