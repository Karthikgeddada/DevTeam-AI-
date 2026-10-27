"""Databricks-workspace-style chrome for the Streamlit app.

Provides:
- inject_databricks_css(): custom CSS that hides Streamlit chrome and styles the
  sidebar (left nav + tree), top bar, tabs, inputs and cards like the Databricks UI.
- brand_markdown(): "DevTeam AI | workspace" header used at the top of the sidebar.
- Navigation callbacks (open_project_callback / open_file_callback / go_workspace).
- open_in_editor(): open a file path in the main editor area.
"""
import streamlit as st


DB_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---- Hide Streamlit chrome ---- */
[data-testid="stHeader"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
footer {display: none;}

/* ---- Base typography / colors ---- */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: #ffffff;
    color: #1f1f1f;
}
.block-container {padding-top: 1.1rem !important; max-width: 100% !important;}

/* ---- Sidebar (left nav + tree panel) ---- */
[data-testid="stSidebar"] {
    background: #fbfbfa !important;
    border-right: 1px solid #e5e5e3 !important;
}
[data-testid="stSidebar"] .block-container {padding-top: 0.7rem !important;}

/* Nav radio rendered as menu items */
[data-testid="stSidebar"] [role="radiogroup"] {gap: 0.15rem;}
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent;
    border-radius: 8px;
    padding: 7px 10px !important;
    margin: 0 !important;
    width: 100%;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background: #ededec;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #e8f0fb;
    box-shadow: inset 3px 0 0 #2563eb;
}
[data-testid="stSidebar"] [role="radiogroup"] label span {
    font-weight: 500;
    font-size: 0.95rem;
}

/* + New button (primary button inside the sidebar) */
[data-testid="stSidebar"] button[kind="primary"] {
    background: #fdeceb;
    color: #c5221f;
    border: 1px solid #f5c6c2;
    border-radius: 8px;
    font-weight: 600;
}

/* ---- Search inputs -> pill style ---- */
[data-testid="stTextInput"] input {
    border-radius: 20px !important;
    background: #f4f4f3;
    border: 1px solid #e3e3e1 !important;
}

/* ---- Buttons ---- */
.stButton > button {border-radius: 8px; font-weight: 500;}

/* ---- Tabs -> browser-tab look ---- */
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid #e5e5e3;}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 6px 14px;
    font-weight: 500;
}
[data-testid="stTabs"] [aria-selected="true"] {background: #e8f0fb; color: #1d4ed8;}

/* ---- Cards / expanders ---- */
[data-testid="stExpander"] {
    border: 1px solid #e9e9e7 !important;
    border-radius: 10px !important;
    background: #ffffff;
}
[data-testid="stMetric"] {
    background: #fafafa;
    border: 1px solid #ececea;
    border-radius: 10px;
    padding: 10px;
}

/* ---- Chat ---- */
[data-testid="stChatInput"] {border: 1px solid #e3e3e1; border-radius: 12px;}
</style>"""


def inject_databricks_css():
    """Inject the Databricks-style CSS. Call once at the top of the workspace."""
    st.markdown(DB_CSS, unsafe_allow_html=True)


def brand_markdown():
    """Sidebar brand header, like the Databricks logo row."""
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;padding:2px 2px 6px 2px;">'
        '<span style="font-size:1.35rem;">🚀</span>'
        '<span style="font-weight:700;font-size:1.05rem;color:#1f1f1f;">DevTeam AI</span>'
        '<span style="font-size:0.72rem;color:#8a8a88;border:1px solid #e3e3e1;'
        'border-radius:10px;padding:1px 8px;">workspace</span></div>',
        unsafe_allow_html=True,
    )


def open_project_callback(pid):
    """Callback: open a project and switch the nav to Workspace."""
    def cb():
        st.session_state.project_id = pid
        st.session_state.current_file = None
        st.session_state["db_nav"] = "🗂️ Workspace"
    return cb


def open_file_callback(path):
    """Callback: open a file in the editor and switch the nav to Workspace."""
    def cb():
        st.session_state.current_file = path
        st.session_state["db_nav"] = "🗂️ Workspace"
    return cb


def go_workspace():
    """Callback: switch the nav to Workspace."""
    st.session_state["db_nav"] = "🗂️ Workspace"


def open_in_editor(services, project_id: str, file_path: str) -> None:
    """Open a project file in the main editor area (used by search results).

    Sets the current file and switches the view to Workspace on the next rerun.
    Must be called from inside an on_click callback, never during rendering.
    """
    st.session_state.project_id = project_id
    st.session_state.current_file = file_path
    st.session_state["db_nav"] = "🗂️ Workspace"
