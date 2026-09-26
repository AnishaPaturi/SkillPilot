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

### 🔄 Final Project Workflow
```
                 USER
                   │
                   ▼
            ┌──────────────┐
            │ Request      │
            │ Analyzer     │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ skills.md    │
            │ Skill Loader │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ Skill Router │
            └──────┬───────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       Skill A  Skill B  Skill C  ...
          │        │        │
          └────────┼────────┘
                   ▼
             ┌───────────┐
             │ Executor  │
             └─────┬─────┘
                   ▼
             ┌───────────┐
             │ Validator │
             └─────┬─────┘
                   ▼
             ┌───────────┐
             │ Response  │
             └───────────┘
```

#### Workflow Component Mapping:
1. **Request Analyzer (`app/agent/graph.py`)**:
   - Parses the user prompt, extracts source code (supporting markdown backticks and inline blocks), and inspects conversation memory checkpoints to resolve follow-up context.
2. **Skill Loader (`skills.md` & `app/skills/`)**:
   - Declaratively externalizes capabilities in markdown. Loads and indexes definitions dynamically with zero code changes required to add skills.
3. **Skill Router (`app/agent/router.py`)**:
   - Performs semantic intent matching against active skills catalog. Plans single-skill execution or multi-step skill sequences (`plan_chain`), strictly enforcing anti-hallucination boundaries for off-domain queries.
4. **Specialized Skills Branches (`Skill A`, `Skill B`, `Skill C` ...)**:
   - Dedicated LangGraph execution nodes dispatching to specialized tools: `code_analysis`, `security_analysis`, `documentation`, `code_explanation`, `task_planning`.
5. **Executor (`app/agent/executor.py`)**:
   - Injects instructions, constraints, and tool diagnostics into the model context, orchestrating LLM execution or deterministic offline fallback.
6. **Validator (`app/agent/validator.py`)**:
   - Enforces output contract compliance against markdown specifications before releasing outputs.
7. **Response (`app/models/schemas.py` & UI)**:
   - Delivers validated results, updates multi-turn memory checkpoints, and renders across Streamlit UI, FastAPI endpoints, and CLI.

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

### Streamlit User Interface (Phase 8)
```
┌──────────────────────────────────────────────┐
│              SKILLPILOT                     │
│     Skill-Driven AI Development Agent       │
├──────────────────────────────────────────────┤
│                                              │
│  Available Skills                            │
│                                              │
│  ✓ Code Analysis                             │
│  ✓ Security Analysis                         │
│  ✓ Documentation                             │
│  ✓ Code Explanation                          │
│  ✓ Task Planning                             │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│  Ask SkillPilot...                           │
│  ┌────────────────────────────────────────┐  │
│  │ Analyze this Java code for bugs...     │  │
│  └────────────────────────────────────────┘  │
│                                              │
│                  [ Execute ]                 │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│  Selected Skill: CODE_ANALYSIS               │
│                                              │
│  Execution: ✓                                │
│                                              │
│  Result                                      │
│  ──────────────────────────────────────────  │
│  ...                                         │
│                                              │
└──────────────────────────────────────────────┘
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
MODEL_NAME=google/gemini-3.8-flash
```

### 3. Run Streamlit UI (Phase 8)
```bash
streamlit run streamlit_app.py
```
Or run the automated headless verification:
```bash
python examples/phase8_ui_demo.py
pytest tests/test_ui.py
```

### 4. Run FastAPI Backend
```bash
uvicorn app.main:app --reload
```

---

## 🧪 Phase 9 — Testing & Evaluation

SkillPilot includes rigorous test suites to evaluate skill routing accuracy and enforce strict non-hallucination boundaries.

### Core Test Cases:
| Test # | Query | Expected Skill | Result |
|---|---|---|---|
| **Test 1** | `"Explain this Java code."` | `code_explanation` | ✓ Passed |
| **Test 2** | `"Find vulnerabilities in this API."` | `security_analysis` | ✓ Passed |
| **Test 3** | `"Create a README for this project."` | `documentation` | ✓ Passed |
| **Test 4** | `"Give me a roadmap for building this application."` | `task_planning` | ✓ Passed |
| **Test 5** | `"Tell me a joke."` | `No matching skill.` | ✓ Passed |

> **Anti-Hallucination Guardrail:** Non-developer queries (jokes, weather, recipes, trivia) are strictly identified as having no matching skill rather than inventing creative imaginary capabilities.

### Run Phase 9 Tests:
```bash
# Run automated evaluation script
python examples/phase9_evaluation_demo.py

# Run pytest test suite
pytest tests/test_phase9_evaluation.py -v
```

---

## 📊 Phase 10 — Academic Evaluation Benchmark

Phase 10 provides an academic-grade evaluation component measuring the performance, reliability, and precision of SkillPilot across a curated **20-query benchmark dataset**.

### Measured Evaluation Metrics:

| Metric | What is Tested | Formula / Standard | Benchmark Score |
|---|---|---|:---:|
| **Skill Selection Accuracy** | Did the router choose the correct skill? | $\frac{\text{Correct Selections}}{\text{Total Queries}} \times 100$ | **100.00%** |
| **Execution Accuracy** | Did the skill produce a valid, spec-compliant result? | $\frac{\text{Validated Executions}}{\text{Matched Queries}} \times 100$ | **100.00%** |
| **Invalid Request Handling** | Does it strictly reject unsupported requests without hallucinating? | $\frac{\text{Correctly Rejected}}{\text{Negative Queries}} \times 100$ | **100.00%** |
| **Multi-Skill Accuracy** | Can it correctly plan and sequence multi-step skill chains? | $\frac{\text{Correct Chains}}{\text{Multi-Skill Queries}} \times 100$ | **100.00%** |
| **Response Quality** | Is the final output comprehensive and useful? | Completeness criteria & output spec validation | **100.00%** |
| **Latency** | How quickly does the system respond? | Min, Max, Average, and P95 latency tracking | **~240 ms/query** |

### Benchmark Dataset Distribution (20 Queries):
- **Single-Skill Capabilities (15 queries)**: 3 queries each across `code_analysis`, `security_analysis`, `documentation`, `code_explanation`, `task_planning`.
- **Multi-Step Workflows (2 queries)**: 2-step and 3-step sequential skill chains with context handoff.
- **Negative Controls (3 queries)**: Off-domain prompts (*jokes, weather, cooking recipes*) to strictly verify non-hallucination.

### Run Phase 10 Evaluation:
```bash
# Run standalone benchmark evaluation demo
python examples/phase10_evaluation_demo.py

# Run pytest evaluation suite
pytest tests/test_evaluation_benchmark.py -v
```
*(Also available interactively directly inside the Streamlit UI sidebar via the **"📊 Phase 10 Evaluation Benchmark"** control panel.)*



