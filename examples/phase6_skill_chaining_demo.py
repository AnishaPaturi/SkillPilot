"""
Phase 6: Multi-Step Skill Chaining Demonstration

Example Query:
"Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."

Pipeline Orchestration:
User Request
     ↓
Skill 1: Security Analysis
     ↓
Intermediate Result (Vulnerabilities & Mitigations)
     ↓
Context Handoff
     ↓
Skill 2: Documentation (Incorporates API code + Security findings)
     ↓
Validated Final Response
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.agent.graph import SkillPilotAgent

SAMPLE_API_CODE = '''from fastapi import FastAPI, HTTPException
import os

app = FastAPI(title="User Management API")
ADMIN_SECRET_KEY = "sk_live_998877665544332211"

@app.post("/users/backup")
def run_backup(path: str):
    # Potential Command Injection
    os.system(f"tar -czf backup.tar.gz {path}")
    return {"status": "backup complete"}

@app.get("/users/query")
def get_user(user_id: str):
    # Potential SQL injection
    sql = "SELECT * FROM users WHERE id = " + user_id
    return {"query": sql}
'''


def run_phase_6_demo():
    print("=" * 80)
    print("PHASE 6: SKILLPILOT MULTI-STEP SKILL CHAINING DEMO")
    print("=" * 80)

    agent = SkillPilotAgent()

    test_queries = [
        {
            "title": "Chained Execution (Security Analysis -> Documentation)",
            "query": "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities.",
            "code": SAMPLE_API_CODE,
        },
        {
            "title": "Chained Execution (Code Review -> Task Planning)",
            "query": "Review this code for bugs and inefficiencies and then break down an implementation plan to refactor it.",
            "code": "def process(items=[]):\n    for i in range(len(items)):\n        print(items[i])",
        },
    ]

    for t in test_queries:
        print("\n" + "=" * 80)
        print(f"Goal: {t['title']}")
        print(f"User Query: \"{t['query']}\"")

        res = agent.run(t["query"], t["code"])

        print("\n[Orchestrator Execution Plan]")
        print(f"  * Planned Skill Chain: {' -> '.join(res.skill_chain)}")
        print(f"  * Total Steps Run    : {len(res.step_results)}")
        for step in res.step_results:
            print(f"      Step {step['step']}: {step['skill_name']} (`{step['skill']}`)")

        print("\n[Combined Response Preview]:")
        lines = res.response.splitlines()
        print("\n".join(lines[:25]))
        if len(lines) > 25:
            print(f"\n... [{len(lines) - 25} more lines generated across chained steps]")

    print("\n" + "=" * 80)
    print("PHASE 6 DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_phase_6_demo()
