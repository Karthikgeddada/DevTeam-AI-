import streamlit as st
import asyncio

from workflows.graph import get_workflow
from providers.errors import ProviderError


TASK_STATUS_COLORS = {
    'pending': '⬜',
    'running': '🔄',
    'awaiting_review': '👀',
    'validating': '✅',
    'completed': '✅',
    'failed': '❌',
    'paused': '⏸️',
    'cancelled': '🚫',
}


def render_task_panel(services):
    """Task progress panel showing plan tasks and execution controls."""
    project_id = st.session_state.project_id
    plan_id = st.session_state.plan_id

    if not plan_id:
        st.info("Submit a request in the Chat tab to create a task plan.")
        return

    workflow = get_workflow()
    tasks = services.task_service.list_tasks(project_id, plan_id)

    if not tasks:
        st.info("No tasks in this plan.")
        return

    # Plan summary
    summary = workflow.get_plan_summary(project_id, plan_id)
    cols = st.columns(4)
    cols[0].metric("Total", summary['total'])
    cols[1].metric("Completed", summary['completed'])
    cols[2].metric("Pending", summary['pending'])
    cols[3].metric("Failed", summary['failed'])

    if summary.get('is_complete'):
        st.success("All tasks completed!")

    # Task list
    st.write("**Tasks:**")
    for i, task in enumerate(tasks):
        icon = TASK_STATUS_COLORS.get(task.status, '⬜')
        with st.expander(f"{icon} Task {i+1}: {task.title}", expanded=(task.status in ('running', 'awaiting_review', 'failed'))):
            st.write(f"**Description:** {task.description}")
            if task.acceptance_criteria:
                st.write(f"**Acceptance:** {task.acceptance_criteria}")
            if task.error:
                st.error(f"Error: {task.error}")

            # Action buttons based on status
            _render_task_actions(services, task, i)


def _render_task_actions(services, task, task_idx):
    """Render action buttons for a task based on its status."""
    project_id = st.session_state.project_id
    plan_id = st.session_state.plan_id
    workflow = get_workflow()
    user_request = st.session_state.user_request
    provider = st.session_state.provider_name
    model = st.session_state.model

    if task.status == 'pending':
        if st.button(f"▶️ Execute", key=f"exec_{task.id}"):
            _execute_task(services, task, user_request, provider, model)

    elif task.status == 'awaiting_review':
        diffs = services.diff_service.get_pending_diffs(project_id)
        task_diffs = [d for d in diffs if d.task_id == task.id]
        st.write(f"**{len(task_diffs)} file changes pending review.**")
        for d in task_diffs:
            st.write(f"  - `{d.file_path}`")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Accept All", key=f"accept_{task.id}", type="primary"):
                result = workflow.accept_task_changes(project_id, task.id)
                if result['success']:
                    st.success(result['message'])
                    if 'validation' in result:
                        val = result['validation']
                        if val['passed']:
                            st.info(f"Validation: {val.get('summary', 'Passed')}")
                        else:
                            st.warning(f"Validation issues: {', '.join(val.get('errors', []))}")
                else:
                    st.error(result['message'])
                    for c in result.get('conflicts', []):
                        st.warning(f"{c['file']}: {c['message']}")
                st.rerun()
        with col2:
            if st.button(f"❌ Reject All", key=f"reject_{task.id}"):
                result = workflow.reject_task_changes(project_id, task.id)
                st.info(f"Rejected {len(result['rejected'])} changes.")
                st.rerun()

    elif task.status == 'failed':
        if st.button(f"🔄 Retry", key=f"retry_{task.id}"):
            _execute_task(services, task, user_request, provider, model)

    elif task.status == 'running':
        if st.button(f"⏸️ Pause", key=f"pause_{task.id}"):
            result = workflow.pause_task(project_id, task.id)
            st.info(result['message'])
            st.rerun()

    elif task.status == 'paused':
        if st.button(f"▶️ Resume", key=f"resume_{task.id}"):
            result = asyncio.run(workflow.resume_task(
                project_id, plan_id, task.id, user_request, provider, model
            ))
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result.get('error', 'Resume failed'))
            st.rerun()

    elif task.status == 'completed':
        st.write("✅ Task completed successfully.")


def _execute_task(services, task, user_request, provider, model):
    """Execute a single task."""
    project_id = st.session_state.project_id
    plan_id = st.session_state.plan_id
    workflow = get_workflow()

    with st.spinner(f"Executing task: {task.title}..."):
        try:
            result = asyncio.run(workflow.execute_task(
                project_id, plan_id, task.id, user_request, provider, model
            ))
            if result['success']:
                st.success(result['message'])
            else:
                error = result.get('error', 'Unknown error')
                if 'category' in result and result['category'] == 'quota_exhaustured':
                    st.warning(f"Quota exhausted: {error}\n\nSwitch providers in the sidebar and retry.")
                else:
                    st.error(f"Task failed: {error}")
        except Exception as e:
            st.error(f"Execution error: {e}")
    st.rerun()