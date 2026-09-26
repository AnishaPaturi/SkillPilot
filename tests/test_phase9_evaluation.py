"""Phase 9: Comprehensive Test Suite for SkillPilot Intent Routing and Non-Hallucination."""
import pytest
from app.skills.registry import SkillRegistry
from app.skills.loader import SkillLoader
from app.agent.router import SkillRouter
from app.agent.graph import SkillPilotAgent


@pytest.fixture
def registry():
    return SkillRegistry(SkillLoader("skills.md"))


@pytest.fixture
def router(registry):
    return SkillRouter(registry=registry)


@pytest.fixture
def agent(registry):
    return SkillPilotAgent(registry=registry)


# ---------------------------------------------------------------------------
# Phase 9 Specification Test Cases: Router Level
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query,expected_skill",
    [
        ("Explain this Java code.", "code_explanation"),
        ("Find vulnerabilities in this API.", "security_analysis"),
        ("Create a README for this project.", "documentation"),
        ("Give me a roadmap for building this application.", "task_planning"),
        ("Tell me a joke.", None),
    ],
    ids=[
        "test1_explain_java_code",
        "test2_find_vulnerabilities",
        "test3_create_readme",
        "test4_give_roadmap",
        "test5_tell_me_a_joke_unmatched",
    ],
)
def test_phase9_router_test_cases(router, query, expected_skill):
    """Verify router matches the 5 Phase 9 test cases without hallucinating skills."""
    selected_skill, supporting = router.route(query)
    assert selected_skill == expected_skill


def test_phase9_test1_code_explanation(router):
    """Test 1: Explain this Java code. -> Expected: code_explanation"""
    skill_id, _ = router.route("Explain this Java code.")
    assert skill_id == "code_explanation"


def test_phase9_test2_security_analysis(router):
    """Test 2: Find vulnerabilities in this API. -> Expected: security_analysis"""
    skill_id, _ = router.route("Find vulnerabilities in this API.")
    assert skill_id == "security_analysis"


def test_phase9_test3_documentation(router):
    """Test 3: Create a README for this project. -> Expected: documentation"""
    skill_id, _ = router.route("Create a README for this project.")
    assert skill_id == "documentation"


def test_phase9_test4_task_planning(router):
    """Test 4: Give me a roadmap for building this application. -> Expected: task_planning"""
    skill_id, _ = router.route("Give me a roadmap for building this application.")
    assert skill_id == "task_planning"


def test_phase9_test5_no_matching_skill(router):
    """
    Test 5: Tell me a joke. -> Expected: No matching skill.
    Ensures agent does not invent a 'joke generation' or conversational skill.
    """
    skill_id, supporting = router.route("Tell me a joke.")
    assert skill_id is None
    assert supporting == []


# ---------------------------------------------------------------------------
# Phase 9 Specification Test Cases: End-to-End Agent Level
# ---------------------------------------------------------------------------

def test_phase9_agent_end_to_end_joke_unmatched(agent):
    """
    Verify agent responds with 'No matching skill.' when given 'Tell me a joke.'
    without hallucinating or executing an unassigned skill.
    """
    res = agent.run("Tell me a joke.")
    assert res.selected_skill is None
    assert res.skill_chain == []
    assert "No matching skill" in res.response or "I don't currently have a skill that matches this request." in res.response


def test_phase9_agent_end_to_end_roadmap(agent):
    """Verify agent executes task_planning skill for roadmap request."""
    res = agent.run("Give me a roadmap for building this application.")
    assert res.selected_skill == "task_planning"
    assert res.is_valid is True
    assert res.response is not None


# ---------------------------------------------------------------------------
# Negative Tests: Ensuring Agent Strictly Rejects Unregistered Capabilities
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "creative_prompt",
    [
        "Tell me a funny joke about programming.",
        "Write a poem about recursive algorithms.",
        "What is the weather in Tokyo right now?",
        "Give me a recipe for authentic Neapolitan pizza.",
        "Who won the 1994 FIFA World Cup?",
    ],
)
def test_no_hallucinated_skills_on_creative_prompts(router, creative_prompt):
    """Verify LLM router strictly returns None for off-domain / non-developer skills."""
    skill_id, _ = router.route(creative_prompt)
    assert skill_id is None, f"Router unexpectedly selected '{skill_id}' for prompt: {creative_prompt}"
