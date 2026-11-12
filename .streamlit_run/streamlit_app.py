"""Temporary launcher for the Cup&Cake Streamlit dashboard."""

from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Cup&Cake | Resultados predictivos",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

dashboard_path = Path(__file__).parents[1] / "dashboard" / "public" / "index.html"
if not dashboard_path.is_file():
    st.error(f"No se encontró el dashboard: {dashboard_path}")
    st.stop()

st.markdown(
    """
    <style>
        .stMainBlockContainer {
            max-width: none;
            padding: 0.75rem 1rem 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.iframe(dashboard_path, height=1100, tab_index=0)
