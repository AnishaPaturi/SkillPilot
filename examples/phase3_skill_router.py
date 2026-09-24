"""
Phase 3: Skill Router Demonstration
Receives user intent and returns structured skill matching with confidence:
{
    "skill": "code_analysis",
    "confidence": 0.94
}
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.registry import SkillRegistry
from app.skills.loader import SkillLoader
from app.agent.router import SkillRouter

if __name__ == "__main__":
    registry = SkillRegistry(SkillLoader("skills.md"))
    router = SkillRouter(registry=registry)

    test_queries = [
        "Review this Java code for bugs.",
        "Scan this repository for hardcoded secrets and security flaws.",
        "Generate a README file and API documentation.",
        "What is the weather in Tokyo?",
    ]

    print("\n[Phase 3] Structured Skill Routing Evaluation:\n")
    for q in test_queries:
        decision = router.route_intent(q)
        print(f"Query: \"{q}\"")
        print(f"Result: {json.dumps(decision, indent=2)}\n")
