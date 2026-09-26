"""
Phase 9: Testing & Evaluation Demonstration

Executes the Phase 9 test cases:
  Test 1: Explain this Java code.                      -> Expected: code_explanation
  Test 2: Find vulnerabilities in this API.            -> Expected: security_analysis
  Test 3: Create a README for this project.            -> Expected: documentation
  Test 4: Give me a roadmap for building this application. -> Expected: task_planning
  Test 5: Tell me a joke.                              -> Expected: No matching skill.

Demonstrating that the agent accurately identifies skills and strictly rejects
off-domain or creative requests (preventing skill hallucination).
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.skills.registry import SkillRegistry
from app.agent.router import SkillRouter
from app.agent.graph import SkillPilotAgent


def run_phase_9_demo():
    print("=" * 80)
    print("PHASE 9: SKILLPILOT ROUTING & ACCURACY EVALUATION DEMO")
    print("=" * 80)

    registry = SkillRegistry()
    router = SkillRouter(registry=registry)
    agent = SkillPilotAgent(registry=registry)

    test_cases = [
        {
            "id": "Test 1",
            "query": "Explain this Java code.",
            "expected_skill": "code_explanation",
            "desc": "Code explanation request on Java source code",
        },
        {
            "id": "Test 2",
            "query": "Find vulnerabilities in this API.",
            "expected_skill": "security_analysis",
            "desc": "Defensive security & vulnerability scan",
        },
        {
            "id": "Test 3",
            "query": "Create a README for this project.",
            "expected_skill": "documentation",
            "desc": "Technical documentation & README generation",
        },
        {
            "id": "Test 4",
            "query": "Give me a roadmap for building this application.",
            "expected_skill": "task_planning",
            "desc": "Implementation planning & engineering roadmap",
        },
        {
            "id": "Test 5",
            "query": "Tell me a joke.",
            "expected_skill": None,
            "desc": "Off-domain query: strictly ensure NO skill is hallucinated",
        },
    ]

    all_passed = True

    for tc in test_cases:
        print("\n" + "-" * 80)
        print(f"{tc['id']}: \"{tc['query']}\"")
        print(f"Goal: {tc['desc']}")
        expected_display = tc['expected_skill'] or "No matching skill."
        print(f"Expected: {expected_display}")

        # Test router level
        routed_skill, _ = router.route(tc["query"])
        actual_display = routed_skill or "No matching skill."

        passed = (routed_skill == tc["expected_skill"])
        status = "PASSED ✓" if passed else "FAILED ❌"
        print(f"Router Decision: {actual_display}  -->  {status}")

        if not passed:
            all_passed = False

    # Also test Test 5 with full end-to-end agent execution
    print("\n" + "-" * 80)
    print("End-to-End Agent Verification for Test 5 ('Tell me a joke.'):")
    res = agent.run("Tell me a joke.")
    print(f"Agent Selected Skill: {res.selected_skill or 'None (No matching skill)'}")
    print(f"Agent Response:\n  \"{res.response.strip()}\"")
    e2e_passed = (res.selected_skill is None) and ("No matching skill" in res.response or "I don't currently have a skill that matches this request." in res.response)
    print(f"End-to-End Evaluation: {'PASSED ✓' if e2e_passed else 'FAILED ❌'}")

    print("\n" + "=" * 80)
    if all_passed and e2e_passed:
        print("ALL PHASE 9 TEST CASES EVALUATED SUCCESSFULLY!")
    else:
        print("SOME CHECKS FAILED.")
    print("=" * 80)


if __name__ == "__main__":
    run_phase_9_demo()
