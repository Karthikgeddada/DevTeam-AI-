import streamlit as st
import asyncio
import time
import uuid

from workflows.graph import get_workflow
from providers.registry import get_registry
from providers.errors import ProviderError, ErrorCategory


def render_chat_panel(services):
    """AI chat panel for submitting requests and viewing conversation."""
    project_id = st.session_state.project_id

    # Show conversation history
    convs = services.repo.get_conversations(project_id)
    if convs:
        for conv in convs[-20:]:  # last 20 messages
            if conv.role == 'user':
                st.chat_message('user').write(conv.content)
            else:
                st.chat_message('assistant').write(conv.content)

    # Chat input
    user_input = st.chat_input("Describe what you want to build or change...")
    if user_input:
        _handle_chat(services, user_input)


def _handle_chat(services, user_input: str):
    """Handle a user chat message."""
    project_id = st.session_state.project_id
    provider_name = st.session_state.provider_name
    model = st.session_state.model

    # Save user message
    from storage.repository import ConversationRecord
    services.repo.save_conversation(ConversationRecord(
        id=str(uuid.uuid4()), project_id=project_id, role='user',
        content=user_input, created_at=time.time(),
    ))

    st.chat_message('user').write(user_input)

    # Check provider availability
    registry = get_registry()
    provider = registry.get_provider(provider_name)
    if not provider or not provider.is_available():
        st.chat_message('assistant').write(
            f"⚠️ No provider available. Please configure {provider_name} API key in Streamlit Secrets.\n\n"
            "See Settings in the sidebar for details."
        )
        return

    # Create plan
    with st.chat_message('assistant'):
        with st.spinner("Planning implementation..."):
            try:
                workflow = get_workflow()
                result = asyncio.run(workflow.plan_tasks(
                    project_id, user_input, provider_name, model
                ))

                st.session_state.plan_id = result['plan_id']
                st.session_state.user_request = user_input

                st.write(f"I've created an implementation plan with {len(result['tasks'])} tasks:")
                for i, task in enumerate(result['tasks']):
                    st.write(f"{i+1}. **{task['title']}** - _{task['description'][:80]}..._" if len(task.get('description', '')) > 80 else f"{i+1}. **{task['title']}** - _{task['description']}_")
                st.write("Switch to the **Tasks** tab to execute each task and review changes.")

            except ProviderError as e:
                _handle_provider_error(e, services, project_id)
            except Exception as e:
                st.error(f"Planning failed: {e}")


def _handle_provider_error(error: ProviderError, services, project_id):
    """Handle provider errors with clear recovery instructions."""
    if error.category == ErrorCategory.AUTH_ERROR:
        st.error(
            f"Authentication error: {error}\n\n"
            "Add your API key to `.streamlit/secrets.toml` and restart."
        )
    elif error.category == ErrorCategory.QUOTA_EXHAUSTED:
        st.warning(
            f"Quota exhausted: {error}\n\n"
            "Your API quota has been used up. Try switching to a different provider.\n"
            "Any accepted changes are preserved."
        )
    elif error.category == ErrorCategory.RATE_LIMIT:
        st.warning(
            f"Rate limit hit: {error}\n\n"
            "Please wait and try again. The request will be retried automatically."
        )
    else:
        st.error(f"Provider error ({error.category.value}): {error}")