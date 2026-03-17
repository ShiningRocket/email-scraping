"""
Light mini-games for Streamlit while waiting on scrapes (all ages).
"""

from __future__ import annotations

import random

import streamlit as st


def _init_session():
    if "game_treasure" not in st.session_state:
        st.session_state.game_treasure = None  # index of treasure 0-8
    if "game_treasure_revealed" not in st.session_state:
        st.session_state.game_treasure_revealed = set()
    if "game_treasure_won" not in st.session_state:
        st.session_state.game_treasure_won = False


def reset_treasure_hunt():
    st.session_state.game_treasure = random.randint(0, 8)
    st.session_state.game_treasure_revealed = set()
    st.session_state.game_treasure_won = False
    st.session_state.game_treasure_digs = 0


def render_treasure_hunt():
    """9 tiles — find the hidden email gem."""
    _init_session()
    if st.session_state.game_treasure is None:
        reset_treasure_hunt()

    st.caption("🗺️ **Treasure dig** — Find the hidden gem in 6 tries or fewer for bragging rights!")
    if st.button("New map", key="th_new"):
        reset_treasure_hunt()
        st.rerun()

    grid = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    for row in grid:
        cols = st.columns(3)
        for col, idx in zip(cols, row):
            with col:
                revealed = idx in st.session_state.game_treasure_revealed
                won = st.session_state.game_treasure_won
                if revealed or won:
                    if idx == st.session_state.game_treasure:
                        label = "💎"
                    else:
                        label = "📭"
                    st.markdown(f"<div style='text-align:center;font-size:2rem;padding:0.5rem'>{label}</div>", unsafe_allow_html=True)
                else:
                    if st.button("Dig", key=f"dig_{idx}"):
                        st.session_state.game_treasure_revealed.add(idx)
                        st.session_state.game_treasure_digs = st.session_state.get("game_treasure_digs", 0) + 1
                        if idx == st.session_state.game_treasure:
                            st.session_state.game_treasure_won = True
                        st.rerun()

    clicks = st.session_state.get("game_treasure_digs", 0)
    if st.session_state.game_treasure_won:
        st.balloons()
        st.success(f"You found the treasure in **{clicks}** dig(s)! The scraper is still working hard for you.")
    elif clicks >= 6 and not st.session_state.game_treasure_won:
        st.warning("Map exhausted — hit **New map** or keep waiting for results!")


def render_emoji_quiz():
    """Quick fun quiz — remote work themed."""
    if "eq_q" not in st.session_state:
        st.session_state.eq_q = random.randint(0, len(_QUIZ) - 1)
        st.session_state.eq_score = 0

    q = _QUIZ[st.session_state.eq_q]
    st.caption("🧠 **Quick quiz** — Tap the best answer!")
    st.markdown(f"**{q['q']}**")

    for i, opt in enumerate(q["opts"]):
        if st.button(opt, key=f"eq_{st.session_state.eq_q}_{i}"):
            if i == q["correct"]:
                st.session_state.eq_score = st.session_state.get("eq_score", 0) + 1
                st.success("Correct! +1")
            else:
                st.info(f"Nice try! Answer: **{q['opts'][q['correct']]}**")
            st.session_state.eq_q = random.randint(0, len(_QUIZ) - 1)
            st.rerun()

    st.caption(f"Score: **{st.session_state.get('eq_score', 0)}**")


_QUIZ = [
    {
        "q": "Which job is super common for remote work worldwide?",
        "opts": ["Underwater welder", "Software developer", "Air traffic controller"],
        "correct": 1,
    },
    {
        "q": "A good remote-work habit is…",
        "opts": ["Never taking breaks", "Clear start/stop times", "Working in bed only"],
        "correct": 1,
    },
    {
        "q": "What does async communication mean?",
        "opts": ["Only video calls", "Reply when you can, not instantly always", "No email ever"],
        "correct": 1,
    },
    {
        "q": "Which skill helps remote careers in the 2020s?",
        "opts": ["Writing clearly online", "Avoiding all tools", "Only voice memos"],
        "correct": 0,
    },
]


def render_rock_paper_scissors():
    st.caption("✊ **Rock · Paper · Scissors** — Best of fun vs the bot!")
    if "rps_w" not in st.session_state:
        st.session_state.rps_w = 0
        st.session_state.rps_l = 0

    choice = st.radio("Your move", ("Rock ✊", "Paper ✋", "Scissors ✌️"), horizontal=True, key="rps_pick")
    if st.button("Play!", key="rps_go"):
        you = ["Rock ✊", "Paper ✋", "Scissors ✌️"].index(choice)
        bot = random.randint(0, 2)
        names = ["Rock", "Paper", "Scissors"]
        win = (you - bot) % 3
        if win == 0:
            st.info(f"Tie! You: {names[you]}, Bot: {names[bot]}")
        elif win == 1:
            st.session_state.rps_w += 1
            st.success(f"You win! Bot chose {names[bot]}")
        else:
            st.session_state.rps_l += 1
            st.warning(f"Bot wins with {names[bot]}")
    st.caption(f"Wins **{st.session_state.rps_w}** · Losses **{st.session_state.rps_l}**")


def render_waiting_games():
    st.subheader("🎮 Play while you wait")
    tab1, tab2, tab3 = st.tabs(["Treasure dig", "Quiz", "Rock Paper Scissors"])
    with tab1:
        render_treasure_hunt()
    with tab2:
        render_emoji_quiz()
    with tab3:
        render_rock_paper_scissors()
