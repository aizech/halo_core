from __future__ import annotations

import streamlit as st


def render(container: st.delta_generator.DeltaGenerator) -> None:
    container.subheader("Advanced")
    container.info(
        "Advanced section scaffolded. Next step: move diagnostics/import-export/reset controls here."
    )
