"""Tests for SkillRouter intent matching."""
import pytest
from app.skills.registry import SkillRegistry
from app.skills.loader import SkillLoader
from app.agent.router import SkillRouter


@pytest.fixture
def router():
    registry = SkillRegistry(SkillLoader("skills.md"))
    return SkillRouter(registry=registry)


def test_route_security_query(router):
    skill_id, supporting = router.route("Analyze this Python code and find security vulnerabilities or issues")
    assert skill_id == "security_analysis"


def test_route_code_review_query(router):
    skill_id, supporting = router.route("Review this code, find bugs and improve performance")
    assert skill_id == "code_analysis"


def test_route_code_explanation(router):
    skill_id, supporting = router.route("Explain this code line by line and tell me how it works")
    assert skill_id == "code_explanation"


def test_route_documentation(router):
    skill_id, supporting = router.route("Generate technical documentation and a README file for my project")
    assert skill_id == "documentation"


def test_route_task_planning(router):
    skill_id, supporting = router.route("Break down the implementation plan and development steps to build a microservice")
    assert skill_id == "task_planning"


def test_route_unmatched_query(router):
    skill_id, supporting = router.route("What is the recipe for chocolate chip cookies?")
    assert skill_id is None


def test_plan_chain_security_and_documentation(router):
    query = "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
    chain = router.plan_chain(query)
    assert chain == ["security_analysis", "documentation"]


def test_plan_chain_three_step_sequence(router):
    query = "Review this code for bugs, then analyze security vulnerabilities, after that generate documentation"
    chain = router.plan_chain(query)
    assert chain == ["code_analysis", "security_analysis", "documentation"]


def test_plan_chain_compound_and(router):
    query = "Analyze this Python code for security issues and generate documentation"
    chain = router.plan_chain(query)
    assert chain == ["security_analysis", "documentation"]


def test_plan_chain_single_step_fallback(router):
    query = "Explain this code line by line and tell me how it works"
    chain = router.plan_chain(query)
    assert chain == ["code_explanation"]


def test_plan_chain_unmatched(router):
    query = "What is the recipe for chocolate chip cookies?"
    chain = router.plan_chain(query)
    assert chain == []
