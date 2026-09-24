"""Tests for skills.md parser, loader, and registry."""
import pytest
from app.skills.parser import SkillsMarkdownParser
from app.skills.loader import SkillLoader
from app.skills.registry import SkillRegistry


def test_parser_parses_all_five_skills():
    loader = SkillLoader("skills.md")
    skills = loader.load_skills()
    assert len(skills) == 5

    skill_ids = [s.id for s in skills]
    expected_ids = [
        "code_analysis",
        "security_analysis",
        "documentation",
        "code_explanation",
        "task_planning",
    ]
    for expected in expected_ids:
        assert expected in skill_ids


def test_security_analysis_spec_integrity():
    loader = SkillLoader("skills.md")
    skills = loader.load_skills()
    sec_skill = next(s for s in skills if s.id == "security_analysis")

    assert sec_skill.name == "Security Analysis"
    assert "Vulnerability" in sec_skill.output_spec
    assert "Severity" in sec_skill.output_spec
    assert "Recommended mitigation" in sec_skill.output_spec
    assert any("exploiting" in c.lower() for c in sec_skill.constraints)


def test_registry_lookup():
    registry = SkillRegistry(SkillLoader("skills.md"))
    skill = registry.get_skill("code_explanation")
    assert skill is not None
    assert skill.id == "code_explanation"
    assert registry.get_skill("non_existent_skill") is None
