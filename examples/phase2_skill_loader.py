"""
Phase 2: Skill Loader Demonstration
Extracts structured skills from skills.md:
[
    {
        "id": "code_analysis",
        "description": "...",
        "when_to_use": [...],
        "input": "...",
        "output": "..."
    }
]
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.loader import load_skills

if __name__ == "__main__":
    skills = load_skills("skills.md")
    print(f"\n[Phase 2] Successfully loaded {len(skills)} skills from skills.md:\n")
    print(json.dumps(skills[:2], indent=2))
    print(f"\n... and {len(skills) - 2} more skills registered.")
