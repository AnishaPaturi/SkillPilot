"""LangGraph State definition for SkillPilot Agent."""
from typing import TypedDict, Optional, List, Dict, Any
from app.models.schemas import SkillDefinition


class AgentState(TypedDict, total=False):
    """The shared state dictionary passing through LangGraph nodes."""
    query: str
    code: Optional[str]
    selected_skill_id: Optional[str]
    supporting_skills: List[str]
    skill_definition: Optional[Dict[str, Any]]
    tool_findings: Optional[Dict[str, Any]]
    raw_response: Optional[str]
    is_valid: bool
    validation_notes: Optional[str]
    error: Optional[str]
    missing_input_prompt: Optional[str]
    final_response: Optional[str]
    retry_count: int
