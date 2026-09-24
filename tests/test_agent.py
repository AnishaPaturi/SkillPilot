"""Tests for end-to-end SkillPilot agent execution."""
import pytest
from app.skills.registry import SkillRegistry
from app.skills.loader import SkillLoader
from app.agent.graph import SkillPilotAgent


@pytest.fixture
def agent():
    registry = SkillRegistry(SkillLoader("skills.md"))
    return SkillPilotAgent(registry=registry)


def test_agent_unmatched_query(agent):
    res = agent.run("Tell me the history of the Roman empire")
    assert res.selected_skill is None
    assert "I don't currently have a skill that matches this request." in res.response


def test_agent_missing_input_prompt(agent):
    res = agent.run("Analyze code for security issues")
    assert res.selected_skill == "security_analysis"
    assert "requires source code" in res.response


def test_agent_security_skill_execution(agent):
    sample_code = """
import os
API_KEY = "my_super_secret_token_12345"
def execute_cmd(user_input):
    os.system("echo " + user_input)
"""
    res = agent.run("Analyze this code for security vulnerabilities", code=sample_code)
    assert res.selected_skill == "security_analysis"
    assert res.is_valid is True
    assert res.response is not None


def test_agent_planning_execution(agent):
    res = agent.run("Provide an implementation plan and development steps to build an authentication service")
    assert res.selected_skill == "task_planning"
    assert res.is_valid is True


def test_agent_skill_chaining(agent):
    query = "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
    code = "import os\nAPI_KEY = 'secret_12345678'\nos.system('echo test')"
    res = agent.run(query, code=code)
    assert res.skill_chain == ["security_analysis", "documentation"]
    assert len(res.step_results) == 2
    assert res.step_results[0]["skill"] == "security_analysis"
    assert res.step_results[1]["skill"] == "documentation"
    assert "Step 1: Security Analysis" in res.response
    assert "Step 2: Documentation" in res.response

