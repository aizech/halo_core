from __future__ import annotations

import streamlit as st

from app import main


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render App design/menu configuration.

    Initial extraction step: delegates to existing implementation.
    """
    main._render_app_design_configuration(container)
