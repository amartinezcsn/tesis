"""Streamlit entry point for the Cup&Cake thesis dashboard."""

from html.parser import HTMLParser
from pathlib import Path

import streamlit as st


class _DashboardDocumentParser(HTMLParser):
    """Extract the self-contained dashboard stored in the iframe srcdoc."""

    def __init__(self) -> None:
        super().__init__()
        self.document: str | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "iframe" or self.document is not None:
            return

        attributes = dict(attrs)
        self.document = attributes.get("srcdoc")


st.set_page_config(
    page_title="Cup&Cake | Resultados predictivos",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

dashboard_path = Path(__file__).parent / "public" / "index.html"
parser = _DashboardDocumentParser()
parser.feed(dashboard_path.read_text(encoding="utf-8"))

if not parser.document:
    st.error("No se pudo cargar el dashboard.")
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

# The repository owns this static HTML. JavaScript execution is required for
# the dashboard's charts and filters, so it is rendered in an isolated iframe.
st.iframe(parser.document, height=1100, tab_index=0)
