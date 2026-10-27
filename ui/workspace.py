import streamlit as st
from config.settings import settings
from providers.registry import get_registry
from ui.project_explorer import render_project_explorer
from ui.code_editor import render_code_editor
from ui.chat_panel import render_chat_panel
from ui.task_panel import render_task_panel
from ui.diff_viewer import render_diff_review


def render_workspace(services):
    """Main workspace layout with sidebar and panels."""
    st.title(f"{settings.APP_ICON} {settings.APP_TITLE}")

    # Sidebar - Project Explorer + Settings
    with st.sidebar:
        st.header("📁 Projects")
        render_project_explorer(services)
        st.divider()
        render_settings(services)

    # Main area - only show if a project is open
    if not st.session_state.project_id:
        st.info("👈 Create or open a project from the sidebar to start coding.")
        _render_welcome(services)
        return

    # Check for provider availability
    registry = get_registry()
    available_providers = [p for p in registry.get_available_providers() if p.available]
    if not available_providers:
        st.warning(
            "⚠️ No LLM provider is configured. AI features will not work.\n\n"
            "Add your API key to Streamlit Secrets (`.streamlit/secrets.toml`):\n"
            "```\n"
            "GEMINI_API_KEY = \"your-key-here\"\n"
            "```")

    # Main layout: two columns - left for editor/explorer, right for chat/tasks
    col_left, col_right = st.columns([3, 2], gap='small')

    with col_left:
        # Tab bar
        tab_editor, tab_diff = st.tabs(["📝 Editor", "🔍 Diff Review"])
        with tab_editor:
            render_code_editor(services)
        with tab_diff:
            render_diff_review(services)

    with col_right:
        tab_chat, tab_tasks = st.tabs(["💬 Chat", "📋 Tasks"])
        with tab_chat:
            render_chat_panel(services)
        with tab_tasks:
            render_task_panel(services)


def render_settings(services):
    """Provider and model selection in sidebar."""
    st.header("⚙️ Settings")
    registry = get_registry()
    providers = registry.get_available_providers()

    provider_names = [p.name for p in providers]
    provider_labels = [f"{p.display_name} ({'available' if p.available else 'not configured'})" for p in providers]

    if not provider_names:
        st.warning("No providers registered.")
        return

    current_idx = 0
    if st.session_state.provider_name in provider_names:
        current_idx = provider_names.index(st.session_state.provider_name)

    selected = st.selectbox(
        "Provider",
        options=range(len(provider_names)),
        format_func=lambda i: provider_labels[i],
        index=current_idx,
        key='provider_select',
    )
    st.session_state.provider_name = provider_names[selected]

    # Model selection
    provider = registry.get_provider(provider_names[selected])
    if provider:
        models = provider.get_models()
        if models:
            model_ids = [m.id for m in models]
            model_labels = [f"{m.name} ({m.id})" for m in models]
            current_model_idx = 0
            if st.session_state.model in model_ids:
                current_model_idx = model_ids.index(st.session_state.model)
            selected_model = st.selectbox(
                "Model",
                options=range(len(model_ids)),
                format_func=lambda i: model_labels[i],
                index=current_model_idx,
                key='model_select',
            )
            st.session_state.model = model_ids[selected_model]


    # Usage summary
    if st.session_state.project_id:
        with st.expander("📊 Usage"):
            usage = services.usage_service.get_usage_summary(st.session_state.project_id)
            st.metric("Total Requests", usage.get('total_requests', 0))
            st.metric("Total Tokens", usage.get('total_tokens', 0))
            est_cost = usage.get('total_cost', 0)
            st.metric("Est. Cost (USD)", f"${est_cost:.4f}")


def _render_welcome(services):
    """Welcome screen with quick actions."""
    st.markdown("""
    ## Welcome to DevTeam AI

    An incremental, persistent AI coding workspace where you can:

    * Create and manage projects with durable persistence
    * Describe changes in natural language
    * Review proposed diffs before applying them
    * Accept or reject changes safely
    * Resume interrupted work after restarts
    * Validate code with static analysis

    **Get started:** Create a new project or open an existing one from the sidebar.
    """)