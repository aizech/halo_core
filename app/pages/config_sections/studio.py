from __future__ import annotations

import streamlit as st


def render(container: st.delta_generator.DeltaGenerator) -> None:
    container.subheader("Studio")
    container.info(
        "Studio section scaffolded. Next step: move action/button controls here."
    )
