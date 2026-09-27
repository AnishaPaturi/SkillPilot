"""Tests for custom skills.md upload, dynamic parsing, and execution."""
import pytest
from app.skills.parser import SkillsMarkdownParser
from app.skills.registry import SkillRegistry
from app.agent.graph import SkillPilotAgent
from fastapi.testclient import TestClient
from app.main import app


SAMPLE_CUSTOM_SKILLS_MD = """# Custom Test Suite Skills

## Unit Test Generator
### Skill ID
unit_test_generator

### Description
Generate comprehensive automated unit test suites for functions and classes.

### When to Use
- Generate unit tests for this function
- Create test suite
- Write unit tests

### Input
Source code of the function or module to test.

### Output
1. Test Suite Implementation
2. Edge Cases Covered
3. Execution Verification

### Constraints
- Prefer standard pytest or unittest frameworks.
- Do not modify source code logic.
"""


def test_custom_markdown_parser():
    """Verify SkillsMarkdownParser correctly parses custom unnumbered skill definitions."""
    validation = SkillsMarkdownParser.validate_markdown(SAMPLE_CUSTOM_SKILLS_MD)
    assert validation["valid"] is True
    assert validation["total_skills"] == 1

    skills = validation["skills"]
    skill = skills[0]
    assert skill.id == "unit_test_generator"
    assert skill.name == "Unit Test Generator"
    assert "Generate comprehensive automated unit test suites" in skill.description
    assert len(skill.when_to_use) >= 2
    assert len(skill.output_spec) == 3
    assert len(skill.constraints) >= 1


def test_registry_custom_skills_load_and_reset():
    """Verify SkillRegistry loads custom markdown content and can restore defaults."""
    registry = SkillRegistry()
    initial_skills_count = len(registry.list_skills())
    assert registry.is_custom is False

    # Load custom markdown
    loaded = registry.load_from_content(SAMPLE_CUSTOM_SKILLS_MD, source_name="my_custom.md")
    assert len(loaded) == 1
    assert registry.is_custom is True
    assert registry.active_source == "my_custom.md"
    assert registry.get_skill("unit_test_generator") is not None

    # Reset back to default
    default_skills = registry.reset_to_default()
    assert len(default_skills) == initial_skills_count
    assert registry.is_custom is False
    assert registry.get_skill("code_analysis") is not None
    assert registry.get_skill("unit_test_generator") is None


def test_agent_routes_and_executes_custom_skill():
    """Verify SkillPilotAgent routes query to custom skill and executes successfully."""
    registry = SkillRegistry()
    registry.load_from_content(SAMPLE_CUSTOM_SKILLS_MD, source_name="custom_suite.md")
    agent = SkillPilotAgent(registry=registry)

    query = "Generate unit tests for this function"
    code = "def multiply(x, y):\n    return x * y"

    response = agent.run(query=query, code=code, session_id="test_custom_thread")
    assert response.selected_skill == "unit_test_generator"
    assert response.is_valid is True
    assert "unit_test_generator" in response.response.lower() or "unit test generator" in response.response.lower()
    assert "exec_custom_skill" in response.active_nodes
    assert len(response.execution_history) == 1


def test_api_upload_and_execute_custom_skill():
    """Verify FastAPI /api/skills/upload and /api/chat handle custom skills."""
    client = TestClient(app)

    # 1. Upload custom skill
    upload_res = client.post(
        "/api/skills/upload",
        json={"content": SAMPLE_CUSTOM_SKILLS_MD, "filename": "uploaded_test.md"},
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["status"] == "success"
    assert "unit_test_generator" in data["skills"]

    # 2. Query agent with the uploaded skill
    chat_res = client.post(
        "/api/chat",
        json={
            "query": "Create test suite for this code",
            "code": "def divide(a, b): return a / b if b != 0 else None",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["selected_skill"] == "unit_test_generator"
    assert chat_data["is_valid"] is True

    # 3. Reset back to default
    reset_res = client.post("/api/skills/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"
