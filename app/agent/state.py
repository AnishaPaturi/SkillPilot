"""LangGraph State definition for SkillPilot Agent with Conversational Memory & Chaining."""
from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    """The shared state dictionary passing through LangGraph nodes."""
    # Phase 7: Core Conversational State & Memory
    messages: List[Dict[str, str]]
    user_request: str
    selected_skill: Optional[str]
    skill_result: Optional[str]
    execution_history: List[Dict[str, Any]]
    session_id: str

    # Pipeline & Processing Fields
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

    # Multi-step Skill Chaining state
    skill_chain: List[str]
    current_step_index: int
    step_results: List[Dict[str, Any]]
    is_chained: bool
