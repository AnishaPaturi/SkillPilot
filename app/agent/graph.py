"""LangGraph Workflow Controller for SkillPilot."""
import os
from typing import Dict, Any, Optional
from app.agent.state import AgentState
from app.agent.router import SkillRouter
from app.agent.executor import SkillExecutor
from app.agent.validator import OutputValidator
from app.skills.registry import SkillRegistry
from app.models.schemas import SkillDefinition, ChatResponse


class SkillPilotAgent:
    """Orchestrates the SkillPilot workflow using LangGraph or direct state machine."""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()
        self.router = SkillRouter(self.registry)
        self._build_workflow()

    def _build_workflow(self):
        """Constructs the LangGraph state machine if langgraph is available, else uses fallback."""
        try:
            from langgraph.graph import StateGraph, END
            workflow = StateGraph(AgentState)

            workflow.add_node("route", self._node_route)
            workflow.add_node("run_tools", self._node_tools)
            workflow.add_node("execute_skill", self._node_execute)
            workflow.add_node("validate", self._node_validate)

            workflow.set_entry_point("route")

            # Conditional routing from router
            workflow.add_conditional_edges(
                "route",
                self._decide_after_route,
                {
                    "no_match": END,
                    "missing_input": END,
                    "proceed": "run_tools",
                },
            )

            workflow.add_edge("run_tools", "execute_skill")
            workflow.add_edge("execute_skill", "validate")
            workflow.add_edge("validate", END)

            self.graph = workflow.compile()
        except ImportError:
            self.graph = None

    def _decide_after_route(self, state: AgentState) -> str:
        if not state.get("selected_skill_id"):
            return "no_match"
        if state.get("missing_input_prompt"):
            return "missing_input"
        return "proceed"

    def _node_route(self, state: AgentState) -> AgentState:
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

        # Check required inputs
        missing_input = None
        requires_code = "code" in skill_def.input_spec.lower() or "source" in skill_def.input_spec.lower()
        has_code = bool(code and code.strip()) or ("```" in query)

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

    def _node_tools(self, state: AgentState) -> AgentState:
        skill_id = state.get("selected_skill_id")
        code = state.get("code")
        if not code and "```" in state.get("query", ""):
            # Extract code block if provided in query
            parts = state["query"].split("```")
            if len(parts) >= 3:
                code = parts[1]
                # Strip language identifier if present
                if "\n" in code:
                    code = code.split("\n", 1)[1]

        findings = SkillExecutor.run_tools_for_skill(
            skill_id, query=state.get("query", ""), code=code
        ) if skill_id else None
        return {**state, "tool_findings": findings, "code": code}

    def _node_execute(self, state: AgentState) -> AgentState:
        skill_dict = state.get("skill_definition")
        if not skill_dict:
            return {**state, "final_response": "No active skill found to execute."}

        skill = SkillDefinition(**skill_dict)
        raw_output = SkillExecutor.execute(
            skill=skill,
            query=state.get("query", ""),
            code=state.get("code"),
            tool_findings=state.get("tool_findings"),
        )
        return {**state, "raw_response": raw_output}

    def _node_validate(self, state: AgentState) -> AgentState:
        skill_dict = state.get("skill_definition")
        raw_output = state.get("raw_response", "")

        if not skill_dict or not raw_output:
            return {**state, "final_response": raw_output, "is_valid": False}

        skill = SkillDefinition(**skill_dict)
        val_result = OutputValidator.validate(skill, raw_output)

        return {
            **state,
            "is_valid": val_result.is_valid,
            "validation_notes": val_result.feedback,
            "final_response": raw_output,
        }

    def run(self, query: str, code: Optional[str] = None) -> ChatResponse:
        """Executes the full agent workflow for a given user query and code."""
        initial_state: AgentState = {
            "query": query,
            "code": code,
            "retry_count": 0,
            "supporting_skills": [],
        }

        if self.graph:
            final_state = self.graph.invoke(initial_state)
        else:
            # Fallback direct execution loop
            s1 = self._node_route(initial_state)
            if self._decide_after_route(s1) != "proceed":
                final_state = s1
            else:
                s2 = self._node_tools(s1)
                s3 = self._node_execute(s2)
                final_state = self._node_validate(s3)

        return ChatResponse(
            success=True,
            selected_skill=final_state.get("selected_skill_id"),
            supporting_skills=final_state.get("supporting_skills", []),
            response=final_state.get("final_response") or "No response generated.",
            is_valid=final_state.get("is_valid", True),
            validation_notes=final_state.get("validation_notes"),
            error=final_state.get("error"),
        )
