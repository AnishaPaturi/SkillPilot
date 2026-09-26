"""Tests for Streamlit UI (Phase 8)."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "streamlit_app.py")


def test_ui_renders_expected_layout():
    """Verify Streamlit app renders header, available skills, and input section."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    assert not at.exception

    # Check header & subtitle
    markdown_texts = [m.value for m in at.markdown]
    all_markdown = "\n".join(markdown_texts)

    assert "SKILLPILOT" in all_markdown
    assert "Skill-Driven AI Development Agent" in all_markdown
    assert "Available Skills" in all_markdown

    # Check that all 5 skills from skills.md are listed with checkmarks
    assert "✓ **Code Analysis**" in all_markdown
    assert "✓ **Security Analysis**" in all_markdown
    assert "✓ **Documentation**" in all_markdown
    assert "✓ **Code Explanation**" in all_markdown
    assert "✓ **Task Planning**" in all_markdown

    # Check Ask SkillPilot section
    assert "Ask SkillPilot..." in all_markdown

    # Check Execute button exists
    execute_btns = [b for b in at.button if b.key == "execute_btn"]
    assert len(execute_btns) == 1


def test_ui_execute_default_query():
    """Verify clicking Execute on default query triggers code analysis and shows results."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    # Click the Execute button
    at.button(key="execute_btn").click().run()

    assert not at.exception
    all_markdown = "\n".join(m.value for m in at.markdown)

    # Verify wireframe result elements
    assert "Selected Skill:" in all_markdown
    assert "CODE_ANALYSIS" in all_markdown
    assert "Execution:" in all_markdown
    assert "✓" in all_markdown
    assert "Result" in all_markdown


def test_ui_reset_memory():
    """Verify clicking Reset Conversation Memory resets session state."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    initial_session_id = at.session_state.session_id
    at.button(key="reset_memory_btn").click().run()

    assert not at.exception
    # Session ID should be renewed
    assert at.session_state.session_id != initial_session_id
    assert len(at.session_state.history) == 0
    assert at.session_state.last_response is None

