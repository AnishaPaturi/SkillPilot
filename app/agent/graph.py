"""LangGraph Workflow Controller for SkillPilot with Multi-Step Skill Chaining.

Architecture:
START
  │
  ▼
Analyze Request
  │
  ▼
Select Skill / Plan Chain
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
                    ┌─────────┴─────────┐
                    │ More in Chain?    │
                    ▼                   ▼
              Advance Chain        Response
              (Context Handoff)         │
                    │                  END
                    └───────► (Next Skill Branch)
"""
import os
from typing import Dict, Any, Optional, List
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
    """Orchestrates the SkillPilot workflow using LangGraph state graph with skill chaining."""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()
        self.router = SkillRouter(self.registry)
        self.graph = self._build_workflow()

    def _build_workflow(self):
        """Constructs the multi-branch and cyclic chaining LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # 1. Ingestion & Router Nodes
        workflow.add_node("analyze_request", self._node_analyze_request)
        workflow.add_node("select_skill", self._node_select_skill)

        # 2. Dedicated Skill Execution Nodes
        workflow.add_node("exec_code_analysis", self._node_exec_code_analysis)
        workflow.add_node("exec_security_analysis", self._node_exec_security_analysis)
        workflow.add_node("exec_documentation", self._node_exec_documentation)
        workflow.add_node("exec_code_explanation", self._node_exec_code_explanation)
        workflow.add_node("exec_task_planning", self._node_exec_task_planning)

        # 3. Validation & Chaining Nodes
        workflow.add_node("validate", self._node_validate)
        workflow.add_node("advance_chain", self._node_advance_chain)
        workflow.add_node("format_response", self._node_format_response)

        # --- Define Flow & Edges ---
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "select_skill")

        # Initial Routing: Branch to skill or exit if no match / missing input
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

        # After validate: Check if there are more skills in the chain
        workflow.add_conditional_edges(
            "validate",
            self._decide_after_validate,
            {
                "advance_chain": "advance_chain",
                "format_response": "format_response",
            },
        )

        # When advancing chain, route to the next skill in the sequence
        workflow.add_conditional_edges(
            "advance_chain",
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

        workflow.add_edge("format_response", END)

        return workflow.compile()

    # --- Node Implementations ---

    def _node_analyze_request(self, state: AgentState) -> AgentState:
        """Analyzes and normalizes user request and extracts embedded code if present."""
        query = state.get("query", "").strip()
        code = state.get("code")

        # Extract code from markdown triple backticks if not provided separately
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
            "step_results": [],
            "current_step_index": 0,
        }

    def _node_select_skill(self, state: AgentState) -> AgentState:
        """Identifies single skill or multi-step skill chain from the user's intent."""
        query = state.get("query", "")
        code = state.get("code")

        # Detect skill chain (e.g., ["security_analysis", "documentation"])
        skill_chain = self.router.plan_chain(query, code)

        if not skill_chain:
            return {
                **state,
                "selected_skill_id": None,
                "skill_chain": [],
                "is_chained": False,
                "final_response": "I don't currently have a skill that matches this request.",
                "is_valid": True,
            }

        first_skill_id = skill_chain[0]
        skill_def = self.registry.get_skill(first_skill_id)

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
            "selected_skill_id": first_skill_id,
            "skill_chain": skill_chain,
            "current_step_index": 0,
            "is_chained": len(skill_chain) > 1,
            "skill_definition": skill_def.model_dump() if skill_def else None,
            "missing_input_prompt": missing_input,
            "final_response": missing_input if missing_input else None,
        }

    def _decide_skill_branch(self, state: AgentState) -> str:
        """Determines which specialized skill execution node to dispatch to."""
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

    def _decide_after_validate(self, state: AgentState) -> str:
        """Determines whether to execute the next skill in the chain or finish."""
        chain = state.get("skill_chain", [])
        curr_idx = state.get("current_step_index", 0)

        if state.get("missing_input_prompt") or not state.get("selected_skill_id"):
            return "format_response"

        # Check if more skills remain in sequence
        if curr_idx + 1 < len(chain):
            return "advance_chain"

        return "format_response"

    def _node_advance_chain(self, state: AgentState) -> AgentState:
        """Advances to the next skill in the chain and injects context from previous steps."""
        curr_idx = state.get("current_step_index", 0) + 1
        chain = state.get("skill_chain", [])
        next_skill_id = chain[curr_idx]
        next_skill_def = self.registry.get_skill(next_skill_id)

        # Context handoff: inject output of previous step into context for next skill
        step_results = state.get("step_results", [])
        prev_output = step_results[-1]["output"] if step_results else ""
        prev_skill = step_results[-1]["skill"] if step_results else "previous step"

        current_code = state.get("code") or ""
        enriched_code = (
            f"{current_code}\n\n"
            f"# ========================================================\n"
            f"# [Context from Prior Step: {prev_skill}]\n"
            f"# ========================================================\n"
            f"{prev_output}"
        )

        return {
            **state,
            "current_step_index": curr_idx,
            "selected_skill_id": next_skill_id,
            "skill_definition": next_skill_def.model_dump() if next_skill_def else None,
            "code": enriched_code,
            "missing_input_prompt": None,
        }

    # --- Dedicated Skill Execution Nodes ---

    def _record_step(self, state: AgentState, output: str, findings: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Appends step output to step_results."""
        results = list(state.get("step_results", []))
        results.append({
            "step": state.get("current_step_index", 0) + 1,
            "skill": state.get("selected_skill_id"),
            "skill_name": state.get("skill_definition", {}).get("name", state.get("selected_skill_id")),
            "output": output,
            "findings": findings,
        })
        return results

    def _node_exec_code_analysis(self, state: AgentState) -> AgentState:
        code = state.get("code", "")
        tool_findings = CodeAnalyzerTool.analyze(code)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=code,
            tool_findings=tool_findings,
        )
        updated_steps = self._record_step(state, output, tool_findings)
        return {**state, "tool_findings": tool_findings, "raw_response": output, "step_results": updated_steps}

    def _node_exec_security_analysis(self, state: AgentState) -> AgentState:
        payload = state.get("code") or state.get("query", "")
        tool_findings = SecurityAnalyzerTool.analyze(payload)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        updated_steps = self._record_step(state, output, tool_findings)
        return {**state, "tool_findings": tool_findings, "raw_response": output, "step_results": updated_steps}

    def _node_exec_documentation(self, state: AgentState) -> AgentState:
        payload = state.get("code") or state.get("query", "")
        tool_findings = DocumentationTool.generate(payload)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        updated_steps = self._record_step(state, output, tool_findings)
        return {**state, "tool_findings": tool_findings, "raw_response": output, "step_results": updated_steps}

    def _node_exec_code_explanation(self, state: AgentState) -> AgentState:
        code = state.get("code", "")
        tool_findings = CodeExplainerTool.explain(code)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=code,
            tool_findings=tool_findings,
        )
        updated_steps = self._record_step(state, output, tool_findings)
        return {**state, "tool_findings": tool_findings, "raw_response": output, "step_results": updated_steps}

    def _node_exec_task_planning(self, state: AgentState) -> AgentState:
        query = state.get("query", "")
        tool_findings = TaskPlannerTool.plan(query)
        skill = SkillDefinition(**state["skill_definition"])

        output = SkillExecutor.execute(
            skill=skill,
            query=query,
            code=state.get("code"),
            tool_findings=tool_findings,
        )
        updated_steps = self._record_step(state, output, tool_findings)
        return {**state, "tool_findings": tool_findings, "raw_response": output, "step_results": updated_steps}

    # --- Validation & Response Nodes ---

    def _node_validate(self, state: AgentState) -> AgentState:
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
        """Synthesizes single-skill response or orchestrated multi-step report."""
        if state.get("missing_input_prompt"):
            return {**state, "final_response": state["missing_input_prompt"]}

        if not state.get("selected_skill_id"):
            return {**state, "final_response": "I don't currently have a skill that matches this request."}

        step_results = state.get("step_results", [])
        if len(step_results) > 1:
            # Multi-step Chained Synthesis
            plan_str = " -> ".join(f"`{s}`" for s in state.get("skill_chain", []))
            lines = [
                "# SkillPilot Multi-Step Execution Pipeline\n",
                f"> **Orchestration Chain:** {plan_str}",
                f"> **Total Steps Executed:** `{len(step_results)}`\n",
            ]
            for step in step_results:
                lines.append(f"## Step {step['step']}: {step['skill_name']} (`{step['skill']}`)")
                lines.append(step["output"])
                lines.append("\n---\n")

            return {**state, "final_response": "\n".join(lines)}

        final_answer = state.get("raw_response") or "No response generated."
        return {**state, "final_response": final_answer}

    def run(self, query: str, code: Optional[str] = None) -> ChatResponse:
        """Runs the compiled LangGraph workflow from START to END."""
        initial_state: AgentState = {
            "query": query,
            "code": code,
            "retry_count": 0,
            "supporting_skills": [],
            "step_results": [],
            "current_step_index": 0,
            "skill_chain": [],
        }

        final_state = self.graph.invoke(initial_state)

        return ChatResponse(
            success=True,
            selected_skill=final_state.get("selected_skill_id"),
            supporting_skills=final_state.get("supporting_skills", []),
            skill_chain=final_state.get("skill_chain", []),
            step_results=final_state.get("step_results", []),
            response=final_state.get("final_response") or "No response generated.",
            is_valid=final_state.get("is_valid", True),
            validation_notes=final_state.get("validation_notes"),
            error=final_state.get("error"),
        )
