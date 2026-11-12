"""Streamlit entry point for the Cup&Cake thesis dashboard."""

from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Cup&Cake | Resultados predictivos",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

dashboard_path = Path(__file__).parent / "public" / "index.html"

if not dashboard_path.is_file():
    st.error(f"No se encontró el dashboard: {dashboard_path}")
    st.stop()

st.iframe(dashboard_path, height=1100, tab_index=0)
