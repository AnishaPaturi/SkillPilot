"""LangGraph Workflow Controller for SkillPilot.

Architecture:
START
  │
  ▼
Analyze Request
  │
  ▼
Select Skill
  │
  ├──── code_analysis ────► Execute
  │
  ├──── security ─────────► Execute
  │
  ├──── documentation ────► Execute
  │
  ├──── explanation ──────► Execute
  │
  └──── planning ─────────► Execute
                              │
                              ▼
                           Validate
                              │
                              ▼
                           Response
                              │
                             END
"""
import os
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.router import SkillRouter
from app.agent.executor import SkillExecutor
from app.agent.validator import OutputValidator
from app.skills.registry import SkillRegistry
from app.models.schemas import SkillDefinition, ChatResponse
from app.tools import (
    CodeAnalyzerTool,
    SecurityAnalyzerTool,
    DocumentationTool,
    CodeExplainerTool,
    TaskPlannerTool,
)


class SkillPilotAgent:
    """Orchestrates the SkillPilot workflow using LangGraph state graph."""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()
        self.router = SkillRouter(self.registry)
        self.graph = self._build_workflow()

    def _build_workflow(self):
        """Constructs the multi-branch LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # 1. Analyze Request Node
        workflow.add_node("analyze_request", self._node_analyze_request)

        # 2. Select Skill (Router) Node
        workflow.add_node("select_skill", self._node_select_skill)

        # 3. Dedicated Skill Execution Nodes
        workflow.add_node("exec_code_analysis", self._node_exec_code_analysis)
        workflow.add_node("exec_security_analysis", self._node_exec_security_analysis)
        workflow.add_node("exec_documentation", self._node_exec_documentation)
        workflow.add_node("exec_code_explanation", self._node_exec_code_explanation)
        workflow.add_node("exec_task_planning", self._node_exec_task_planning)

        # 4. Output Validation Node
        workflow.add_node("validate", self._node_validate)

        # 5. Format Response Node
        workflow.add_node("format_response", self._node_format_response)

        # --- Define Edges & Flow ---
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "select_skill")

        # Conditional branching from Select Skill
        workflow.add_conditional_edges(
            "select_skill",
            self._decide_skill_branch,
            {
                "code_analysis": "exec_code_analysis",
                "security_analysis": "exec_security_analysis",
                "documentation": "exec_documentation",
                "code_explanation": "exec_code_explanation",
                "task_planning": "exec_task_planning",
                "no_match": "format_response",
                "missing_input": "format_response",
            },
        )

        # All execution branches converge into validate
        workflow.add_edge("exec_code_analysis", "validate")
        workflow.add_edge("exec_security_analysis", "validate")
        workflow.add_edge("exec_documentation", "validate")
        workflow.add_edge("exec_code_explanation", "validate")
        workflow.add_edge("exec_task_planning", "validate")

        # Validation moves to response formatting
        workflow.add_edge("validate", "format_response")

        # Response moves to END
        workflow.add_edge("format_response", END)

        return workflow.compile()

    # --- Node Implementations ---

    def _node_analyze_request(self, state: AgentState) -> AgentState:
        """Analyzes and normalizes user request and extracts embedded code if present."""
        query = state.get("query", "").strip()
        code = state.get("code")

        # If code not passed separately, extract from markdown triple backticks
        if not code and "```" in query:
            parts = query.split("```")
            if len(parts) >= 3:
                extracted = parts[1].strip()
                if "\n" in extracted:
                    extracted = extracted.split("\n", 1)[1]
                code = extracted

        return {
            **state,
            "query": query,
            "code": code,
        }

    def _node_select_skill(self, state: AgentState) -> AgentState:
        """Selects the most relevant skill using the SkillRouter."""
        query = state.get("query", "")
        code = state.get("code")

        skill_id, supporting = self.router.route(query, code)

        if not skill_id:
            return {
                **state,
                "selected_skill_id": None,
                "final_response": "I don't currently have a skill that matches this request.",
                "is_valid": True,
            }

        skill_def = self.registry.get_skill(skill_id)
        if not skill_def:
            return {
                **state,
                "selected_skill_id": None,
                "final_response": "I don't currently have a skill that matches this request.",
                "is_valid": True,
            }

        # Validate required inputs
        missing_input = None
        requires_code = "code" in skill_def.input_spec.lower() or "source" in skill_def.input_spec.lower()
        has_code = bool(code and code.strip())

        if requires_code and not has_code:
            missing_input = (
                f"The '{skill_def.name}' skill requires source code to analyze. "
                "Please provide the relevant code or configuration."
            )

        return {
            **state,
            "selected_skill_id": skill_id,
            "supporting_skills": supporting,
            "skill_definition": skill_def.model_dump(),
            "missing_input_prompt": missing_input,
            "final_response": missing_input if missing_input else None,
        }

    def _decide_skill_branch(self, state: AgentState) -> str:
        """Routes execution to the matching dedicated skill node."""
        if not state.get("selected_skill_id"):
            return "no_match"
        if state.get("missing_input_prompt"):
            return "missing_input"

        skill_id = state["selected_skill_id"]
        valid_branches = {
            "code_analysis",
            "security_analysis",
            "documentation",
            "code_explanation",
            "task_planning",
        }
        return skill_id if skill_id in valid_branches else "no_match"

    # --- Dedicated Skill Execution Nodes ---

    def _node_exec_code_analysis(self, state: AgentState) -> AgentState:
        """Executes Code Analysis: Input -> code; Output -> bugs + improvements."""
        code = state.get("code", "")
        tool_findings = CodeAnalyzerTool.analyze(code)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=code,
            tool_findings=tool_findings,
        )
        return {**state, "tool_findings": tool_findings, "raw_response": output}

    def _node_exec_security_analysis(self, state: AgentState) -> AgentState:
        """Executes Security Analysis: Input -> source/config; Output -> vulnerabilities + mitigations."""
        payload = state.get("code") or state.get("query", "")
        tool_findings = SecurityAnalyzerTool.analyze(payload)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        return {**state, "tool_findings": tool_findings, "raw_response": output}

    def _node_exec_documentation(self, state: AgentState) -> AgentState:
        """Executes Documentation: Input -> project/code; Output -> documentation."""
        payload = state.get("code") or state.get("query", "")
        tool_findings = DocumentationTool.generate(payload)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        return {**state, "tool_findings": tool_findings, "raw_response": output}

    def _node_exec_code_explanation(self, state: AgentState) -> AgentState:
        """Executes Code Explanation: Input -> code; Output -> explanation."""
        code = state.get("code", "")
        tool_findings = CodeExplainerTool.explain(code)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=code,
            tool_findings=tool_findings,
        )
        return {**state, "tool_findings": tool_findings, "raw_response": output}

    def _node_exec_task_planning(self, state: AgentState) -> AgentState:
        """Executes Task Planning: Input -> requirement; Output -> implementation plan."""
        query = state.get("query", "")
        tool_findings = TaskPlannerTool.plan(query)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=query,
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        return {**state, "tool_findings": tool_findings, "raw_response": output}

    # --- Validation & Response Nodes ---

    def _node_validate(self, state: AgentState) -> AgentState:
        """Validates output against skill output specifications and constraints."""
        skill_dict = state.get("skill_definition")
        raw_output = state.get("raw_response", "")

        if not skill_dict or not raw_output:
            return {**state, "is_valid": False, "validation_notes": "No output generated"}

        skill = SkillDefinition(**skill_dict)
        val_result = OutputValidator.validate(skill, raw_output)

        return {
            **state,
            "is_valid": val_result.is_valid,
            "validation_notes": val_result.feedback,
        }

    def _node_format_response(self, state: AgentState) -> AgentState:
        """Finalizes response formatting."""
        final_answer = (
            state.get("raw_response")
            or state.get("missing_input_prompt")
            or state.get("final_response")
            or "No response generated."
        )
        return {
            **state,
            "final_response": final_answer,
        }

    def run(self, query: str, code: Optional[str] = None) -> ChatResponse:
        """Runs the compiled LangGraph workflow from START to END."""
        initial_state: AgentState = {
            "query": query,
            "code": code,
            "retry_count": 0,
            "supporting_skills": [],
        }

        final_state = self.graph.invoke(initial_state)

        return ChatResponse(
            success=True,
            selected_skill=final_state.get("selected_skill_id"),
            supporting_skills=final_state.get("supporting_skills", []),
            response=final_state.get("final_response") or "No response generated.",
            is_valid=final_state.get("is_valid", True),
            validation_notes=final_state.get("validation_notes"),
            error=final_state.get("error"),
        )
