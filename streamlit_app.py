"""Streamlit UI for SkillPilot matching the Phase 8 specification."""
import streamlit as st
import os
import uuid
from dotenv import load_dotenv

from app.skills.registry import SkillRegistry
from app.agent.graph import SkillPilotAgent

load_dotenv()

st.set_page_config(
    page_title="SkillPilot | Skill-Driven AI Development Agent",
    page_icon="🧭",
    layout="centered",
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
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = "Analyze this Java code for bugs..."
if "code_input" not in st.session_state:
    st.session_state.code_input = ""

# Sidebar: Controls & Multi-Turn History
with st.sidebar:
    st.title("🧭 SkillPilot Controls")
    st.caption("Runtime Configuration & Session Memory")

    st.markdown("### 🧠 Conversation Memory")
    st.caption(f"Session Thread: `{st.session_state.session_id}`")
    st.caption(f"Turns in Memory: `{len(st.session_state.history)}`")

    if st.button("🗑️ Reset Conversation Memory", use_container_width=True, key="reset_memory_btn"):
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
        st.session_state.history = []
        st.session_state.last_response = None
        st.session_state.prompt_input = "Analyze this Java code for bugs..."
        st.session_state.code_input = ""
        st.success("Started new session!")
        st.rerun()

    if st.button("🔄 Reload skills.md", use_container_width=True, key="reload_skills_btn"):
        st.session_state.registry.reload()
        st.session_state.agent = SkillPilotAgent(registry=st.session_state.registry)
        st.success("Reloaded skills.md successfully!")
        st.rerun()

    with st.expander("📊 Phase 10 Evaluation Benchmark"):
        st.caption("Measure accuracy, latency, and rejection rate on 20 benchmark queries.")
        if st.button("🚀 Run Evaluation Suite", use_container_width=True, key="run_benchmark_btn"):
            from app.evaluation.benchmark import EvaluationBenchmark
            bench = EvaluationBenchmark(agent=st.session_state.agent)
            with st.spinner("Evaluating benchmark dataset..."):
                summary = bench.evaluate_router_only()
                st.session_state["benchmark_summary"] = summary
            st.success("Benchmark Completed!")

        if "benchmark_summary" in st.session_state:
            sm = st.session_state["benchmark_summary"]
            st.metric("Skill Selection Accuracy", f"{sm.skill_selection_accuracy:.1f}%")
            st.metric("Invalid Request Handling", f"{sm.invalid_request_handling:.1f}%")
            st.metric("Multi-Skill Accuracy", f"{sm.multi_skill_accuracy:.1f}%")
            st.metric("Avg Latency", f"{sm.avg_latency_ms:.1f} ms")


    if st.session_state.history:
        st.divider()
        st.markdown("### 📜 Prior Turns")
        for item in st.session_state.history:
            st.markdown(f"**Turn {item['turn']}:** `{item['user_request']}`")
            st.caption(f"Executed: `{item['selected_skill']}`")

# Header Section
st.markdown("<h1 style='text-align: center; margin-bottom: 2px; font-weight: 800; letter-spacing: 0.05em;'>SKILLPILOT</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #888; margin-top: 0px; margin-bottom: 18px; font-weight: normal;'>Skill-Driven AI Development Agent</h4>", unsafe_allow_html=True)
st.divider()

# Section 1: Available Skills
st.markdown("### Available Skills")
skills = st.session_state.registry.list_skills()
for skill in skills:
    st.markdown(f"✓ **{skill.name}**")

st.divider()

# Section 2: Ask SkillPilot...
st.markdown("### Ask SkillPilot...")

# Quick sample chips for one-click testing
sample_cols = st.columns(3)
if sample_cols[0].button("🐞 Java Bug Scan", use_container_width=True, key="chip_java"):
    st.session_state.prompt_input = "Analyze this Java code for bugs..."
    st.session_state.code_input = """public class UserManager {
    private List<String> users = new ArrayList<>();
    public void addUser(String user) {
        users.add(user);
    }
}"""
elif sample_cols[1].button("🔒 Security & Docs Chain", use_container_width=True, key="chip_security"):
    st.session_state.prompt_input = "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
    st.session_state.code_input = """import os
API_KEY = "sk_live_secret_key"
def run(cmd):
    os.system(cmd)
"""
elif sample_cols[2].button("💬 Memory Follow-up", use_container_width=True, key="chip_memory"):
    st.session_state.prompt_input = "Now document those issues."
    st.session_state.code_input = ""

query_text = st.text_area(
    "Query",
    value=st.session_state.prompt_input,
    placeholder="Analyze this Java code for bugs...",
    height=100,
    label_visibility="collapsed",
    key="query_area",
)

with st.expander("📎 Optional: Code or Configuration Snippet", expanded=bool(st.session_state.code_input)):
    code_text = st.text_area(
        "Code Snippet",
        value=st.session_state.code_input,
        placeholder="Paste source code or configuration here (optional if included in prompt or relying on prior turn memory)...",
        height=140,
        label_visibility="collapsed",
        key="code_area",
    )

_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    execute_button = st.button("Execute", type="primary", use_container_width=True, key="execute_btn")

# Execution Action
if execute_button:
    eff_query = query_text.strip() if query_text else ""
    if not eff_query:
        st.warning("Please enter a query or request for SkillPilot.")
    else:
        with st.spinner("SkillPilot routing and executing..."):
            response = st.session_state.agent.run(
                query=eff_query,
                code=code_text.strip() if code_text and code_text.strip() else None,
                session_id=st.session_state.session_id,
            )
            st.session_state.last_response = response
            st.session_state.history = response.execution_history

# Section 3: Result Display (matching Phase 8 wireframe)
if st.session_state.last_response:
    res = st.session_state.last_response
    st.divider()

    skill_display = (res.selected_skill or "UNKNOWN").upper()
    if res.skill_chain and len(res.skill_chain) > 1:
        chain_display = " ➔ ".join(s.upper() for s in res.skill_chain)
        st.markdown(f"**Selected Skill:** `{chain_display}`")
    else:
        st.markdown(f"**Selected Skill:** `{skill_display}`")

    status_icon = "✓" if res.is_valid else "⚠️"
    st.markdown(f"**Execution:** {status_icon}")

    st.markdown("### Result")
    st.markdown("──────────────────────────────────────────")
    st.markdown(res.response)

    if res.validation_notes:
        st.info(f"**Validation Feedback:** {res.validation_notes}")
