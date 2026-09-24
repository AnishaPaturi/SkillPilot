"""
Phase 5: LangGraph Multi-Branch Workflow Demonstration

Visualizes and executes the full agentic graph:
START -> Analyze Request -> Select Skill -> [Branch to Skill] -> Validate -> Response -> END
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.graph import SkillPilotAgent


def run_phase_5_demo():
    print("=" * 75)
    print("PHASE 5: LANGGRAPH AGENTIC WORKFLOW DEMONSTRATION")
    print("=" * 75)

    agent = SkillPilotAgent()

    # 1. Print compiled graph topology
    print("\n--- COMPILED LANGGRAPH TOPOLOGY (Mermaid) ---")
    print(agent.graph.get_graph().draw_mermaid())

    # 2. Test Scenarios
    scenarios = [
        {
            "name": "Scenario A: Security Analysis Branch",
            "query": "Scan this Python script for hardcoded secrets and command injection vulnerabilities.",
            "code": "import os\nAPI_KEY = 'sk_live_12345678abcdef'\nos.system('echo test')",
        },
        {
            "name": "Scenario B: Code Analysis Branch",
            "query": "Review this function for bugs and bad practices.",
            "code": "def process(items=[]):\n    try:\n        return items[0]\n    except:\n        pass",
        },
        {
            "name": "Scenario C: Task Planning Branch",
            "query": "How to build a distributed task worker queue using Redis and Python?",
            "code": None,
        },
        {
            "name": "Scenario D: Missing Input Handling",
            "query": "Review my code for performance bugs.",
            "code": None,  # Code is missing!
        },
        {
            "name": "Scenario E: Unmatched Intent Fallback",
            "query": "What is the recipe for baking sourdough bread?",
            "code": None,
        },
    ]

    for sc in scenarios:
        print("\n" + "=" * 75)
        print(f"Executing {sc['name']}")
        print(f"Query: \"{sc['query']}\"")
        if sc['code']:
            print(f"Code provided: {len(sc['code'].splitlines())} lines")

        response = agent.run(sc["query"], sc["code"])

        print(f"\n[Agent Decision]")
        print(f"  • Selected Skill  : {response.selected_skill or 'None (Fallback)'}")
        print(f"  • Validated Output: {'Yes' if response.is_valid else 'No'}")
        if response.validation_notes:
            print(f"  • Validation Notes: {response.validation_notes}")

        print(f"\n[Response Summary]:")
        response_preview = "\n".join(response.response.splitlines()[:10])
        print(response_preview)
        if len(response.response.splitlines()) > 10:
            print("  ... (truncated for display)")

    print("\n" + "=" * 75)
    print("PHASE 5 WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    run_phase_5_demo()
