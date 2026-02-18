from __future__ import annotations

import streamlit as st

from app import main


def render(container: st.delta_generator.DeltaGenerator) -> None:
    main._render_studio_configuration(container)
