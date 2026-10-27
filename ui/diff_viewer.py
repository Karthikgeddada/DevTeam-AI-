import streamlit as st
from services.diff_service import DiffService


def render_diff_review(services):
    """Diff review panel showing proposed and applied changes."""
    project_id = st.session_state.project_id
    if not project_id:
        st.info("Open a project to review changes.")
        return

    diffs = services.diff_service.get_diffs_for_project(project_id)
    if not diffs:
        st.info("No file changes yet. Execute tasks to generate changes.")
        return

    # Filter tabs
    tab_pending, tab_accepted, tab_history = st.tabs(["Pending", "Accepted", "History"])

    pending = [d for d in diffs if d.status == 'proposed']
    accepted = [d for d in diffs if d.status == 'accepted']
    all_diffs = diffs

    with tab_pending:
        _render_diff_list(services, pending, "pending")
    with tab_accepted:
        _render_diff_list(services, accepted, "accepted")
    with tab_history:
        _render_diff_list(services, all_diffs, "history")


def _render_diff_list(services, diffs, mode):
    """Render a list of diffs with accept/reject/revert controls."""
    if not diffs:
        st.write("_No changes in this category._")
        return

    for d in diffs:
        with st.expander(f"{'🟡' if d.status == 'proposed' else '🟢' if d.status == 'accepted' else '🔴'} {d.file_path} ({d.status})", expanded=(d.status == 'proposed')):
            # Show diff text
            if d.diff_text:
                st.code(d.diff_text, language='diff')
            else:
                st.write("(no changes)")

            # Side by side for proposed
            if d.status == 'proposed' and d.base_content is not None:
                col_old, col_new = st.columns(2)
                with col_old:
                    st.write("**Base:**")
                    st.code(d.base_content[:2000], language='text')
                with col_new:
                    st.write("**Proposed:**")
                    st.code(d.proposed_content[:2000], language='text')

                # Accept/reject (only in the Pending tab so element keys stay unique)
                if mode == "pending":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Accept", key=f"diff_accept_{d.id}"):
                            try:
                                success, msg, _ = services.diff_service.accept_diff_for_project(
                                    d.project_id, d.id
                                )
                                if success:
                                    st.success(msg)
                                else:
                                    st.warning(msg)
                            except Exception as e:
                                st.warning(f"Could not accept change: {e}")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject", key=f"diff_reject_{d.id}"):
                            try:
                                success, msg = services.diff_service.reject_diff(
                                    d.project_id, d.id
                                )
                                if success:
                                    st.info(msg)
                                else:
                                    st.warning(msg)
                            except Exception as e:
                                st.warning(f"Could not reject change: {e}")
                            st.rerun()

            elif d.status == 'accepted' and mode == 'accepted':
                if st.button(f"⏪ Revert", key=f"diff_revert_{d.id}"):
                    try:
                        success, msg = services.diff_service.revert_diff(
                            d.project_id, d.id
                        )
                        if success:
                            st.info(msg)
                        else:
                            st.warning(msg)
                    except Exception as e:
                        st.warning(f"Could not revert change: {e}")
                    st.rerun()