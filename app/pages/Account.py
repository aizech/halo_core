from __future__ import annotations

import streamlit as st

from app import main
from services import user_memory


def render_account_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()
    st.title("Account")
    st.caption("Manage your profile and preferences.")
    user_id = user_memory.resolve_user_id(st.session_state)
    st.subheader("Memory")
    st.caption(f"Active user: `{user_id}`")

    if not user_memory.is_memory_backend_enabled():
        st.info("Memory backend disabled (set HALO_AGENT_DB).")
        return

    user_memory.ensure_memory_schema_if_needed()
    memories = user_memory.list_user_memories(user_id=user_id)

    if not memories:
        st.info("No memories found yet.")
    else:
        selected_state = st.session_state.setdefault("account_memory_selection", {})
        table_data = {
            "Select": [
                bool(selected_state.get(memory.memory_id, False)) for memory in memories
            ],
            "Memory": [memory.memory_text for memory in memories],
            "Topics": [", ".join(memory.topics) for memory in memories],
            "Created": [memory.created_at for memory in memories],
        }
        edited = st.data_editor(
            table_data,
            width="stretch",
            hide_index=True,
            key="account_memory_editor",
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", width="small"),
                "Memory": st.column_config.TextColumn("Memory", disabled=True),
                "Topics": st.column_config.TextColumn("Topics", disabled=True),
                "Created": st.column_config.TextColumn("Created", disabled=True),
            },
        )
        for idx, selected in enumerate(edited["Select"]):
            selected_state[memories[idx].memory_id] = bool(selected)

    selected_ids = [
        memory.memory_id
        for memory in memories
        if st.session_state.get("account_memory_selection", {}).get(
            memory.memory_id, False
        )
    ]

    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
    with col1:
        if st.button("Refresh", key="account_mem_refresh", width="stretch"):
            st.rerun()
    with col2:
        if st.button(
            f"Delete selected ({len(selected_ids)})",
            key="account_mem_delete_selected",
            width="stretch",
            disabled=not selected_ids,
        ):
            result = user_memory.delete_user_memories(
                user_id=user_id, memory_ids=selected_ids
            )
            if result.deleted_count:
                st.success(f"Deleted {result.deleted_count} memories.")
            if result.failed_ids:
                st.error("Failed IDs: " + ", ".join(result.failed_ids))
            st.session_state["account_memory_selection"] = {}
            st.rerun()
    with col3:
        if st.button(
            "Clear all",
            key="account_mem_clear_all",
            width="stretch",
            type="primary",
            disabled=not memories,
        ):
            result = user_memory.clear_user_memories(user_id=user_id)
            if result.deleted_count:
                st.success(f"Cleared {result.deleted_count} memories.")
            if result.failed_ids:
                st.error("Failed IDs: " + ", ".join(result.failed_ids))
            st.session_state["account_memory_selection"] = {}
            st.rerun()


if __name__ == "__main__":
    render_account_page()
