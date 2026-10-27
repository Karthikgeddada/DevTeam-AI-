import streamlit as st
from security.path_validator import is_safe_filename


def render_project_explorer(services):
    """Sidebar project explorer: create, open, list, import/export."""
    # Create new project
    with st.expander("➕ New Project", expanded=False):
        name = st.text_input("Project Name", key="new_project_name")
        desc = st.text_input("Description", key="new_project_desc")
        lang = st.selectbox("Language", ["python", "javascript", "typescript", "go", "rust"], key="new_project_lang")
        if st.button("Create", key="create_project_btn", type="primary"):
            if name:
                project = services.project_service.create_project(name, desc, lang)
                st.session_state.project_id = project.id
                st.session_state.current_file = None
                st.session_state.plan_id = None
                st.success(f"Created project: {name}")
                st.rerun()
            else:
                st.warning("Please enter a project name.")

    # List existing projects
    projects = services.project_service.list_projects()
    if projects:
        st.write("**Open Project:**")
        for p in projects:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📂 {p.name}", key=f"proj_{p.id}", use_container_width=True):
                    st.session_state.project_id = p.id
                    st.session_state.current_file = None
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{p.id}", help="Delete project"):
                    services.project_service.delete_project(p.id)
                    if st.session_state.project_id == p.id:
                        st.session_state.project_id = None
                    st.rerun()

        # Rename current project
        if st.session_state.project_id:
            current = services.project_service.get_project(st.session_state.project_id)
            if current:
                with st.expander("✏️ Rename"):
                    new_name = st.text_input("New name", value=current.name, key="rename_input")
                    if st.button("Rename", key="rename_btn"):
                        services.project_service.rename_project(current.id, new_name)
                        st.rerun()
    else:
        st.write("_No projects yet._")

    # Import/Export
    if st.session_state.project_id:
        st.divider()
        with st.expander("📦 Import / Export"):
            uploaded = st.file_uploader("Import ZIP", type=['zip'], key="import_zip")
            if uploaded and st.button("Import", key="import_btn"):
                try:
                    files = services.project_service.import_zip(
                        st.session_state.project_id, uploaded.getvalue()
                    )
                    st.success(f"Imported {len(files)} files")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

            if st.button("Export as ZIP", key="export_btn"):
                try:
                    zip_path = services.project_service.export_zip(st.session_state.project_id)
                    with open(zip_path, 'rb') as f:
                        st.download_button(
                            "Download ZIP", f,
                            file_name=f"{services.project_service.get_project(st.session_state.project_id).name}.zip",
                            mime='application/zip',
                        )
                except Exception as e:
                    st.error(f"Export failed: {e}")

        # File tree for current project
        st.divider()
        _render_file_tree(services)


def _render_file_tree(services):
    """Render file tree for the current project in the sidebar."""
    files = services.project_service.list_files(st.session_state.project_id)
    if not files:
        st.write("_No files yet._")
        with st.expander("New File"):
            _new_file_form(services)
        return

    # File search
    search_query = st.text_input("Search files...", key="file_search", placeholder="Filter by name")
    if search_query:
        files = services.project_service.search_files(st.session_state.project_id, search_query)

    st.write("**Files:**")
    for f in files:
        path = f.get('path', '')
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            if st.button(path, key=f"file_{path}", use_container_width=True):
                st.session_state.current_file = path
                st.rerun()
        with col2:
            if st.button("Rename", key=f"rn_{path}", help="Rename file"):
                st.session_state[f"renaming_{path}"] = True
                st.rerun()
        with col3:
            if st.button("X", key=f"rm_{path}", help="Delete file"):
                services.project_service.delete_file(st.session_state.project_id, path)
                if st.session_state.current_file == path:
                    st.session_state.current_file = None
                st.rerun()

        # Inline rename form
        if st.session_state.get(f"renaming_{path}"):
            new_name = st.text_input("New path", value=path, key=f"rename_input_{path}")
            col_rn_save, col_rn_cancel = st.columns(2)
            with col_rn_save:
                if st.button("Save", key=f"rename_save_{path}", type="primary"):
                    try:
                        services.project_service.rename_file(
                            st.session_state.project_id, path, new_name
                        )
                        st.session_state.pop(f"renaming_{path}", None)
                        if st.session_state.current_file == path:
                            st.session_state.current_file = new_name
                        st.success(f"Renamed to {new_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Rename failed: {e}")
            with col_rn_cancel:
                if st.button("Cancel", key=f"rename_cancel_{path}"):
                    st.session_state.pop(f"renaming_{path}", None)
                    st.rerun()

    with st.expander("New File"):
        _new_file_form(services)


def _new_file_form(services):
    """Form for creating a new file."""
    file_path = st.text_input("File path (e.g. src/main.py)", key="new_file_path")
    if st.button("Create File", key="create_file_btn"):
        if not file_path:
            st.warning("Enter a file path.")
            return
        try:
            services.project_service.save_file(
                st.session_state.project_id, file_path, "# New file\n", created_by="user"
            )
            st.session_state.current_file = file_path
            st.success(f"Created {file_path}")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create file: {e}")