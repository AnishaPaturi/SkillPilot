"""
Phase 7: Conversational State & Memory Demonstration

Scenario:
Turn 1:
  User: "Analyze this code."
  Code: def fetch_data(cache=[]): ...
  Agent: [Executes code_analysis and stores findings in memory]

Turn 2:
  User: "Now document those issues."
  Code: None (No code provided! Agent retrieves code and analysis from memory)
  Agent: [Executes documentation referencing Turn 1 findings]

Turn 3:
  User: "Explain that line by line."
  Code: None (Agent uses code from memory)
  Agent: [Executes code_explanation on the cached code]
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.agent.graph import SkillPilotAgent

SAMPLE_CODE = """def process_transactions(records=[]):
    try:
        total = 0
        for i in range(len(records)):
            if records[i] == True:
                total += 1
        return total
    except:
        pass
"""


def run_phase_7_demo():
    print("=" * 80)
    print("PHASE 7: SKILLPILOT CONVERSATIONAL MEMORY & STATE DEMONSTRATION")
    print("=" * 80)

    agent = SkillPilotAgent()
    session_id = "user_session_42"

    # --- TURN 1 ---
    print("\n" + "=" * 80)
    print("[TURN 1]")
    print('User: "Analyze this code for bugs and inefficiencies."')
    print("Input: Source code provided with mutable default arg and bare except.")

    res_turn1 = agent.run(
        query="Analyze this code for bugs and inefficiencies.",
        code=SAMPLE_CODE,
        session_id=session_id,
    )

    print(f"\nAgent (Skill: {res_turn1.selected_skill}):")
    print(res_turn1.response[:350] + "\n  ... [truncated]")
    print(f"Memory Check: Total turns in history = {len(res_turn1.execution_history)}")

    # --- TURN 2 ---
    print("\n" + "=" * 80)
    print("[TURN 2]")
    print('User: "Now document those issues."')
    print("Input: No code provided! (Relying on Conversational Memory)")

    res_turn2 = agent.run(
        query="Now document those issues.",
        code=None,  # Intentionally None!
        session_id=session_id,
    )

    print(f"\nAgent (Skill: {res_turn2.selected_skill}):")
    print(f"  • Successfully resolved context from memory without prompt error!")
    print(f"  • Total turns in history: {len(res_turn2.execution_history)}")
    print("\nResponse Preview:")
    print("\n".join(res_turn2.response.splitlines()[:18]))

    # --- TURN 3 ---
    print("\n" + "=" * 80)
    print("[TURN 3]")
    print('User: "Explain that line by line."')
    print("Input: No code provided! (Relying on Conversational Memory)")

    res_turn3 = agent.run(
        query="Explain that line by line.",
        code=None,  # Intentionally None!
        session_id=session_id,
    )

    print(f"\nAgent (Skill: {res_turn3.selected_skill}):")
    print(f"  • Total turns in history: {len(res_turn3.execution_history)}")
    print("\nResponse Preview:")
    print("\n".join(res_turn3.response.splitlines()[:15]))

    print("\n" + "=" * 80)
    print("PHASE 7 MEMORY DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_phase_7_demo()
