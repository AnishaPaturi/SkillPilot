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
    # Verify Step 2 documentation incorporates vulnerabilities from Step 1
    assert "Vulnerabilit" in res.step_results[1]["output"]
    assert res.is_valid is True


def test_agent_three_step_chaining(agent):
    query = "Review this code for bugs, then analyze security vulnerabilities, after that generate documentation"
    code = "import os\nAPI_KEY = 'secret_12345678'\ndef bad(items=[]):\n    os.system('echo ' + str(items))\n"
    res = agent.run(query, code=code)
    assert res.skill_chain == ["code_analysis", "security_analysis", "documentation"]
    assert len(res.step_results) == 3
    assert res.step_results[0]["skill"] == "code_analysis"
    assert res.step_results[1]["skill"] == "security_analysis"
    assert res.step_results[2]["skill"] == "documentation"
    assert res.is_valid is True


def test_agent_chaining_missing_input(agent):
    query = "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
    res = agent.run(query, code=None)
    assert res.skill_chain == ["security_analysis", "documentation"]
    assert "requires source code" in res.response


def test_agent_conversational_memory(agent):
    session_id = "test_memory_thread_1"
    code = "def calc(items=[]):\n    return sum(items)"

    # Turn 1
    t1 = agent.run("Analyze this code for bugs", code=code, session_id=session_id)
    assert t1.selected_skill == "code_analysis"
    assert len(t1.execution_history) == 1

    # Turn 2: Follow-up without passing code explicitly
    t2 = agent.run("Now document those issues", code=None, session_id=session_id)
    assert t2.selected_skill == "documentation"
    assert len(t2.execution_history) == 2
    assert "requires source code" not in t2.response


