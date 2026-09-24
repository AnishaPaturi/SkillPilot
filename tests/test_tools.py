"""Unit tests for Phase 4 specialized tools."""
import pytest
from app.tools import (
    CodeAnalyzerTool,
    SecurityAnalyzerTool,
    DocumentationTool,
    CodeExplainerTool,
    TaskPlannerTool,
)


def test_code_analyzer_tool():
    bad_code = """
def test_fn(items=[]):
    try:
        val = 1
    except:
        pass
"""
    result = CodeAnalyzerTool.analyze(bad_code)
    assert "bugs" in result
    assert "improvements" in result
    assert any(b["type"] == "MutableDefaultArgument" for b in result["bugs"])
    assert any("bare" in imp.lower() or "explicit" in imp.lower() for imp in result["improvements"])


def test_security_analyzer_tool():
    vulnerable_code = """
import os
SECRET_TOKEN = "sk_live_12345678abcdefg"
def run(cmd):
    os.system("echo " + cmd)
"""
    result = SecurityAnalyzerTool.analyze(vulnerable_code)
    assert "vulnerabilities" in result
    assert "mitigations" in result
    vuln_types = [v["vulnerability"] for v in result["vulnerabilities"]]
    assert "Hardcoded Secret" in vuln_types
    assert "Command Injection" in vuln_types
    assert len(result["mitigations"]) >= 2


def test_documentation_tool():
    code = """
class Calculator:
    '''Simple math calculator.'''
    def add(self, a, b):
        '''Adds two numbers.'''
        return a + b
"""
    result = DocumentationTool.generate(code)
    assert "markdown_doc" in result
    doc = result["markdown_doc"]
    assert "## 1. Overview" in doc
    assert "## 2. Features" in doc
    assert "## 3. Architecture" in doc
    assert "## 4. Installation" in doc
    assert "## 5. Usage" in doc
    assert "## 6. Configuration" in doc
    assert "## 7. Examples" in doc


def test_code_explainer_tool():
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
    result = CodeExplainerTool.explain(code)
    assert "high_level_explanation" in result
    assert "step_by_step_execution" in result
    assert "important_concepts" in result
    assert any("Recursion" in c for c in result["important_concepts"])


def test_task_planner_tool():
    requirement = "Build a REST API backend with user authentication and PostgreSQL"
    result = TaskPlannerTool.plan(requirement)
    assert "goal" in result
    assert "requirements" in result
    assert "implementation_phases" in result
    assert len(result["implementation_phases"]) >= 3
    assert "dependencies" in result
    assert "testing_strategy" in result
