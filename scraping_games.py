"""
Games while waiting on scrapes — embedded arcade (see arcade_games.py).
"""

from __future__ import annotations

from arcade_games import render_arcade


def render_waiting_games() -> None:
    render_arcade(height=520)
