import streamlit as st
from config.settings import settings
from providers.registry import get_registry
from ui.databricks_ui import (
    inject_databricks_css,
    brand_markdown,
    open_project_callback,
    open_file_callback,
    go_workspace,
)
from ui.project_explorer import render_project_explorer
from ui.code_editor import render_code_editor
from ui.chat_panel import render_chat_panel
from ui.task_panel import render_task_panel
from ui.diff_viewer import render_diff_review

NAV_ITEMS = ["🏠 Home", "🗂️ Workspace", "🕑 Recents", "🗃️ Projects", "⚙️ Settings"]


def render_workspace(services):
    """Databricks-style layout: left nav + tree sidebar, top bar, main views."""
    inject_databricks_css()

    # Sidebar - brand, + New, nav, tree panel, settings
    with st.sidebar:
        brand_markdown()
        if st.button(
            "＋ New",
            key="db_new_btn",
            use_container_width=True,
            on_click=lambda: st.session_state.update(
                {"show_new_project": not st.session_state.get("show_new_project", False)}
            ),
        ):
            pass
        st.radio("Navigation", NAV_ITEMS, key="db_nav", label_visibility="collapsed")
        st.divider()
        st.caption("**TREE VIEW**")
        render_project_explorer(services)
        st.divider()
        render_settings(services)

    # Top bar (Databricks-style: view title, global search, avatar)
    query = _render_topbar(services)
    if query:
        _render_search_results(services, query)
        return

    # Main views
    view = st.session_state.get("db_nav", NAV_ITEMS[0])
    if view == "🏠 Home":
        _render_home(services)
    elif view == "🗂️ Workspace":
        _render_main(services)
    elif view == "🕑 Recents":
        _render_recents(services)
    elif view == "🗃️ Projects":
        _render_projects(services)
    else:
        _render_settings_page(services)


def _render_topbar(services):
    """Databricks-style top bar: view title, global search, avatar."""
    left, mid, right = st.columns([1.6, 4.2, 1.0], vertical_alignment="center")
    with left:
        view = st.session_state.get("db_nav", NAV_ITEMS[0])
        parts = view.split(" ", 1)
        st.markdown(f"### {parts[0]} {parts[1] if len(parts) > 1 else ''}")
    with mid:
        query = st.text_input(
            "Search",
            key="db_top_search",
            placeholder="🔍  Search projects, files, and more...",
            label_visibility="collapsed",
        )
    with right:
        project_id = st.session_state.get("project_id")
        proj = services.project_service.get_project(project_id) if project_id else None
        initial = (proj.name if proj else "U")[:1].upper()
        st.markdown(
            "<div style='text-align:right;'>"
            "<span style='display:inline-flex;width:34px;height:34px;border-radius:50%;"
            "background:#2563eb;color:#fff;align-items:center;justify-content:center;"
            f"font-weight:700;'>{initial}</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<hr style='margin:2px 0 10px 0;padding:0;border:none;border-top:1px solid #e5e5e3;'>",
        unsafe_allow_html=True,
    )
    return (query or "").strip()


def _render_search_results(services, query):
    """Global search results across projects and files in the open project."""
    st.markdown(f"#### Search results for “{query}”")
    q = query.lower()
    projects = [
        p for p in services.project_service.list_projects() if q in p.name.lower()
    ]
    if projects:
        st.write("**Projects**")
        for p in projects:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"🗂️ **{p.name}** — _{p.description or 'No description'}_")
            with c2:
                st.button(
                    "Open",
                    key=f"srch_open_{p.id}",
                    on_click=open_project_callback(p.id),
                    use_container_width=True,
                )
    project_id = st.session_state.get("project_id")
    files = []
    if project_id:
        try:
            files = services.project_service.search_files(project_id, query)
        except Exception:
            files = []
    if files:
        st.write("**Files in current project**")
        for f in files:
            path = f.get("path", "")
            st.button(
                f"📄 {path}",
                key=f"srch_file_{path}",
                on_click=open_file_callback(path),
                use_container_width=True,
            )
    if not projects and not files:
        st.caption("No matching projects or files.")


def _render_home(services):
    """Home view: welcome, quick stats, and shortcuts."""
    st.markdown("## 👋 Welcome to DevTeam AI")
    st.markdown(
        "An incremental, persistent AI coding workspace where you can:"
        "\n\n* Create and manage projects with durable persistence"
        "\n* Describe changes in natural language"
        "\n* Review proposed diffs before applying them"
        "\n* Accept or reject changes safely"
        "\n* Resume interrupted work after restarts"
    )
    projects = services.project_service.list_projects()
    m1, m2, m3 = st.columns(3)
    m1.metric("Projects", len(projects))
    total_files = sum(len(services.project_service.list_files(p.id)) for p in projects)
    m2.metric("Files tracked", total_files)
    m3.metric("AI provider", settings.DEFAULT_PROVIDER.title())
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 🗂️ Workspace")
            st.caption("Open the editor, chat with the AI team, and review tasks.")
            st.button(
                "Open Workspace",
                key="home_open_ws",
                on_click=go_workspace,
                use_container_width=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown("### 🕑 Recents")
            st.caption("Jump back into a recent project.")
            st.button(
                "View Recents",
                key="home_recents",
                on_click=lambda: st.session_state.update({"db_nav": "🕑 Recents"}),
                use_container_width=True,
            )
    with c3:
        with st.container(border=True):
            st.markdown("### 🗃️ Projects")
            st.caption("Browse all projects, or use ＋ New in the sidebar.")
            st.button(
                "Go to Projects",
                key="home_projects",
                on_click=lambda: st.session_state.update({"db_nav": "🗃️ Projects"}),
                use_container_width=True,
            )


def _render_main(services):
    """The coding workspace: editor + diff review left, chat + tasks right."""
    if not st.session_state.project_id:
        st.info("👈 Create or open a project from the sidebar to start coding.")
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

    col_left, col_right = st.columns([3, 2], gap='small')

    with col_left:
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


def _render_recents(services):
    """Recently updated projects."""
    st.markdown("## 🕑 Recents")
    projects = services.project_service.list_projects()
    if not projects:
        st.caption("No projects yet. Create one with ＋ New in the sidebar.")
        return
    for p in projects[:10]:
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        with c1:
            st.markdown(
                f"🗂️ **{p.name}**  \n_{p.description or 'No description'}_ · `{p.language}`"
            )
        with c2:
            st.button(
                "Open",
                key=f"rec_open_{p.id}",
                on_click=open_project_callback(p.id),
                use_container_width=True,
            )


def _render_projects(services):
    """All projects as a card grid."""
    st.markdown("## 🗃️ Projects")
    projects = services.project_service.list_projects()
    if not projects:
        st.caption("No projects yet. Create one with ＋ New in the sidebar.")
        return
    cols = st.columns(3)
    for i, p in enumerate(projects):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### 🗂️ {p.name}")
                st.caption(p.description or "No description")
                st.caption(f"Language: `{p.language}`")
                st.button(
                    "Open project",
                    key=f"pv_open_{p.id}",
                    on_click=open_project_callback(p.id),
                    use_container_width=True,
                )


def _render_settings_page(services):
    """Settings page: provider status and usage summary."""
    st.markdown("## ⚙️ Settings")
    registry = get_registry()
    for p in registry.get_available_providers():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{p.display_name}**")
            with c2:
                if p.available:
                    st.markdown("🟢 Available")
                else:
                    st.markdown("⚪ Not configured")
    st.info(
        "Configure provider API keys in Streamlit Secrets (`.streamlit/secrets.toml`) "
        "or environment variables, then restart the app."
    )
    if st.session_state.project_id:
        st.divider()
        st.markdown("### 📊 Usage for current project")
        try:
            usage = services.usage_service.get_usage_summary(st.session_state.project_id)
            u1, u2, u3 = st.columns(3)
            u1.metric("Total requests", usage.get("total_requests", 0))
            u2.metric("Total tokens", usage.get("total_tokens", 0))
            u3.metric("Est. cost (USD)", f"${usage.get('total_cost', 0):.4f}")
        except Exception as e:
            st.warning(f"Could not load usage: {e}")


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
    """Welcome shim kept for compatibility; renders the Home view."""
    _render_home(services)