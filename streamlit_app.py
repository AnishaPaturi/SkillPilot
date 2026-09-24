"""Streamlit UI for SkillPilot with Conversational Memory & Multi-Step Chaining."""
import streamlit as st
import os
import uuid
from dotenv import load_dotenv

from app.skills.loader import SkillLoader
from app.skills.registry import SkillRegistry
from app.agent.graph import SkillPilotAgent

load_dotenv()

st.set_page_config(
    page_title="SkillPilot | Skill-Driven AI Agent",
    page_icon="🧭",
    layout="wide",
)

# Initialize Session State
if "registry" not in st.session_state:
    st.session_state.registry = SkillRegistry()
if "agent" not in st.session_state:
    st.session_state.agent = SkillPilotAgent(registry=st.session_state.registry)
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar: Skill Catalog & Memory Management
with st.sidebar:
    st.title("🧭 Skill Catalog")
    st.caption("Capabilities loaded dynamically from `skills.md`")

    skills = st.session_state.registry.list_skills()
    st.write(f"**Total Skills Loaded:** `{len(skills)}`")

    for s in skills:
        with st.expander(f"🔹 {s.name} (`{s.id}`)"):
            st.markdown(f"**Description:** {s.description}")
            st.markdown(f"**Input:** `{s.input_spec}`")
            st.markdown("**Triggers:**")
            for t in s.when_to_use[:3]:
                st.caption(f"- {t}")
            st.markdown("**Required Output:**")
            for out in s.output_spec:
                st.caption(f"- {out}")

    st.divider()
    st.markdown("### 🧠 Conversation Memory")
    st.caption(f"Session Thread: `{st.session_state.session_id}`")
    st.caption(f"Turns in Memory: `{len(st.session_state.history)}`")

    if st.button("🗑️ Reset Conversation Memory", use_container_width=True):
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
        st.session_state.history = []
        st.success("Started new conversation session!")

    if st.button("🔄 Reload skills.md", use_container_width=True):
        st.session_state.registry.reload()
        st.session_state.agent = SkillPilotAgent(registry=st.session_state.registry)
        st.success("Reloaded skills.md successfully!")

# Main Panel
st.title("🧭 SkillPilot")
st.subheader("Skill-Driven Autonomous Agent Runtime")
st.markdown(
    "SkillPilot dynamically matches requests to skills in `skills.md`, chains sequential tasks, "
    "and maintains conversation memory across multi-turn dialogs."
)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 💬 Request Input")
    
    # Predefined sample buttons
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    preset_query = ""
    preset_code = ""

    if sample_col1.button("Security Scan"):
        preset_query = "Analyze this Python code and find security vulnerabilities"
        preset_code = """import os
API_KEY = "sk_live_999888777666555444"

def run_backup(user_path):
    os.system("tar -czf backup.tar.gz " + user_path)
"""
    if sample_col2.button("Chained Request"):
        preset_query = "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
        preset_code = """import os
ADMIN_KEY = "secret_token_12345"
def query_db(uid):
    return "SELECT * FROM users WHERE id=" + uid
"""
    if sample_col3.button("Follow-up Turn"):
        preset_query = "Now document those issues."
        preset_code = ""

    user_query = st.text_area(
        "User Prompt / Goal",
        value=preset_query,
        placeholder="e.g. Analyze this Python code or 'Now document those issues'",
        height=100,
    )

    user_code = st.text_area(
        "Source Code / Configuration (Optional - memory retains prior code)",
        value=preset_code,
        placeholder="Paste code or config here (can leave blank for follow-up questions)...",
        height=200,
    )

    submit = st.button("🚀 Execute Request", type="primary", use_container_width=True)

with col2:
    st.markdown("### ⚡ Execution & Response")

    if submit:
        if not user_query.strip():
            st.warning("Please enter a query or request.")
        else:
            with st.spinner("SkillPilot reasoning and executing..."):
                response = st.session_state.agent.run(
                    query=user_query,
                    code=user_code if user_code.strip() else None,
                    session_id=st.session_state.session_id,
                )
                st.session_state.history = response.execution_history

            # Metadata bar
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                skill_badge = response.selected_skill or "None (Fallback)"
                st.metric(label="Active Skill", value=skill_badge)
            with meta_col2:
                status_badge = "✅ Valid" if response.is_valid else "⚠️ Needs Review"
                st.metric(label="Output Status", value=status_badge)
            with meta_col3:
                chain_info = " -> ".join(response.skill_chain) if len(response.skill_chain) > 1 else "Single Step"
                st.metric(label="Execution Mode", value=chain_info)

            st.divider()
            st.markdown(response.response)

            if response.validation_notes:
                st.info(f"**Validation Feedback:** {response.validation_notes}")

    # Prior turns accordion
    if st.session_state.history:
        with st.expander(f"📜 View Conversation Memory ({len(st.session_state.history)} prior turns)"):
            for item in st.session_state.history:
                st.markdown(f"**Turn {item['turn']} Prompt:** `{item['user_request']}`")
                st.caption(f"Skill Executed: `{item['selected_skill']}`")
                st.divider()
