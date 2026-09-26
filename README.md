# SkillPilot 🧭

**SkillPilot** is a skill-driven autonomous AI agent runtime built with **FastAPI**, **LangGraph**, and **Pydantic**. Instead of rigid, hardcoded if-else routing, SkillPilot dynamically discovers, selects, loads instructions for, and executes skills defined in markdown (`skills.md`).

---

## 🌟 Core Concepts

- **Declarative Skills**: Capabilities are externalized in `skills.md`. Adding a new skill requires zero changes to agent control code.
- **Agent Controller**: Built with LangGraph for stateful multi-step cycles: routing, execution, validation, and correction loops.
- **Dynamic Routing**: Uses LLM semantic intent matching against skill definitions to select the appropriate capability.
- **Output Validation**: Enforces skill-specific output contracts via Pydantic models before returning results.
- **Multi-Step Skill Chaining**: Orchestrates sequential multi-skill execution workflows (e.g., Security Analysis → Documentation).
- **Conversational Memory (Phase 7)**: Stateful multi-turn dialog tracking via LangGraph checkpointer, maintaining `messages`, `user_request`, `selected_skill`, `skill_result`, and `execution_history`.

---

## 🏗️ Architecture

### Single-Skill Flow
```
User Request
     ↓
FastAPI Endpoint
     ↓
Agent Controller (LangGraph)
     ↓
Skill Loader (skills.md)
     ↓
Skill Router
     ↓
Specialized Skill Execution (code_analysis, security_analysis, task_planning, etc.)
     ↓
Output Validator
     ↓
Validated Response
```

### Multi-Step Skill Chaining (Phase 6)
```
User Request
     ↓
Skill 1: Security Analysis
     ↓
Result / Context Handoff
     ↓
Skill 2: Documentation
     ↓
Final Result
```

### Conversational Memory Across Turns (Phase 7)
```
Turn 1:
User: "Analyze this code."
     ↓
Agent executes Skill 1 (code_analysis)
     ↓
AgentState records:
  • messages
  • user_request
  • selected_skill
  • skill_result (detected bugs / issues)
  • execution_history

Turn 2:
User: "Now document those issues." (No code provided)
     ↓
Agent retrieves Turn 1 skill_result & code from AgentState
     ↓
Agent executes Skill 2 (documentation) explaining Turn 1 issues
```

---

## 🚀 Quickstart

### 1. Installation
Using `uv`:
```bash
uv venv
.venv\Scripts\activate  # Windows
uv pip install -r requirements.txt
```

### 2. Environment Setup
Configure your OpenRouter API key in `.env`:
```ini
OPENROUTER_API_KEY=your_key_here
MODEL_NAME=google/gemini-2.0-flash-001
```

### 3. Run FastAPI Backend
```bash
uvicorn app.main:app --reload
```

### 4. Run Streamlit UI
```bash
streamlit run streamlit_app.py
```
