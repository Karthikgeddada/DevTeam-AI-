import streamlit as st
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from services.persistence import get_services
from ui.workspace import render_workspace


def main():
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon=settings.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize services (triggers schema creation)
    services = get_services()

    # Initialize session state
    if 'project_id' not in st.session_state:
        st.session_state.project_id = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'plan_id' not in st.session_state:
        st.session_state.plan_id = None
    if 'provider_name' not in st.session_state:
        st.session_state.provider_name = settings.DEFAULT_PROVIDER
    if 'model' not in st.session_state:
        st.session_state.model = settings.DEFAULT_MODEL
    if 'view' not in st.session_state:
        st.session_state.view = 'workspace'
    if 'unsaved_changes' not in st.session_state:
        st.session_state.unsaved_changes = {}
    if 'user_request' not in st.session_state:
        st.session_state.user_request = ''

    # Render the main workspace
    render_workspace(services)


if __name__ == '__main__':
    main()