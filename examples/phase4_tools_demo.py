"""
Phase 4: Tool Execution Demonstration
Demonstrates the 5 specialized tools:
1. Code Analysis       (Input: source code   -> Output: bugs + improvements)
2. Security Analysis   (Input: source/config -> Output: vulnerabilities + mitigations)
3. Documentation       (Input: project/code  -> Output: documentation)
4. Code Explanation    (Input: code          -> Output: explanation)
5. Task Planning       (Input: requirement   -> Output: implementation plan)
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import (
    CodeAnalyzerTool,
    SecurityAnalyzerTool,
    DocumentationTool,
    CodeExplainerTool,
    TaskPlannerTool,
)

SAMPLE_CODE = '''def fetch_user_data(user_id, cache=[]):
    """Fetches user data and caches results."""
    try:
        if user_id == None:
            return None
        cache.append(user_id)
        for i in range(len(cache)):
            print(f"Index {i}: {cache[i]}")
        return {"id": user_id, "active": True}
    except:
        pass
'''

SAMPLE_SECURITY_CODE = '''import os
API_KEY = "sk_live_999888777666555444"
DATABASE_URL = "postgres://admin:password@localhost:5432/prod"

def delete_user_record(user_id):
    # Dynamic SQL concatenation
    query = "DELETE FROM users WHERE id = " + user_id
    os.system("echo Deleting user " + user_id)
'''

SAMPLE_REQUIREMENT = "Build a real-time collaborative document editor with WebSocket synchronization and JWT authentication."


def run_phase_4_demo():
    print("=" * 70)
    print("PHASE 4: SKILLPILOT SPECIALIZED TOOLS DEMONSTRATION")
    print("=" * 70)

    # 1. Code Analysis Tool
    print("\n--- 1. CODE ANALYSIS TOOL ---")
    print("Input: Source code with mutable default arg, range(len), bare except")
    analysis_res = CodeAnalyzerTool.analyze(SAMPLE_CODE)
    print(f"Bugs Detected: {len(analysis_res['bugs'])}")
    for b in analysis_res['bugs']:
        print(f"  • [{b['type']}] Line {b.get('line')}: {b['description']}")
    print(f"Improvements Suggested: {len(analysis_res['improvements'])}")
    for imp in analysis_res['improvements']:
        print(f"  • {imp}")

    # 2. Security Analysis Tool
    print("\n--- 2. SECURITY ANALYSIS TOOL ---")
    print("Input: Code with hardcoded secrets, SQL injection, and command injection")
    sec_res = SecurityAnalyzerTool.analyze(SAMPLE_SECURITY_CODE)
    print(f"Vulnerabilities Found: {len(sec_res['vulnerabilities'])}")
    for v in sec_res['vulnerabilities']:
        print(f"  • [{v['severity']}] {v['vulnerability']} at line {v['line']}: {v['explanation']}")
    print(f"Mitigations: {len(sec_res['mitigations'])}")
    for m in sec_res['mitigations']:
        print(f"  • {m}")

    # 3. Documentation Tool
    print("\n--- 3. DOCUMENTATION TOOL ---")
    print("Input: Source code snippet")
    doc_res = DocumentationTool.generate(SAMPLE_CODE)
    print(f"Generated Document: '{doc_res['title']}'")
    print(f"Sections Included: Overview, Features, Architecture, Installation, Usage, Config, Examples")
    print("Preview:\n" + "\n".join(doc_res['markdown_doc'].splitlines()[:16]) + "\n...")

    # 4. Code Explanation Tool
    print("\n--- 4. CODE EXPLANATION TOOL ---")
    print("Input: Source code snippet")
    expl_res = CodeExplainerTool.explain(SAMPLE_CODE)
    print("High-Level Explanation:", expl_res['high_level_explanation'])
    print(f"Step-by-Step Walkthrough ({len(expl_res['step_by_step_execution'])} steps):")
    for step in expl_res['step_by_step_execution'][:3]:
        print(f"  • {step}")
    print("Important Concepts:", ", ".join(expl_res['important_concepts']))

    # 5. Task Planning Tool
    print("\n--- 5. TASK PLANNING TOOL ---")
    print(f"Input Requirement: '{SAMPLE_REQUIREMENT}'")
    plan_res = TaskPlannerTool.plan(SAMPLE_REQUIREMENT)
    print("Goal:", plan_res['goal'])
    print(f"Phases Planned: {len(plan_res['implementation_phases'])}")
    for p in plan_res['implementation_phases']:
        print(f"  • {p['phase']} ({len(p['tasks'])} tasks)")
    print("Dependencies:", ", ".join(plan_res['dependencies']))
    print("=" * 70)


if __name__ == "__main__":
    run_phase_4_demo()
