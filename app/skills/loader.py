"""File loader for skills.md."""
import os
from pathlib import Path
from typing import List
from app.models.schemas import SkillDefinition
from app.skills.parser import SkillsMarkdownParser


class SkillLoader:
    """Loads and watches skills.md from the file system."""

    def __init__(self, file_path: str = "skills.md"):
        self.file_path = Path(file_path)

    def load_skills(self) -> List[SkillDefinition]:
        """Reads skills.md and returns the parsed list of SkillDefinition objects."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Skills specification file not found at: {self.file_path.resolve()}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return SkillsMarkdownParser.parse(content)


def load_skills(file_path: str = "skills.md") -> list[dict]:
    """Reads skills.md and returns a list of skill dictionaries matching Phase 2 spec."""
    loader = SkillLoader(file_path)
    skills = loader.load_skills()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "when_to_use": s.when_to_use,
            "input": s.input_spec,
            "output": s.output_spec,
            "constraints": s.constraints,
        }
        for s in skills
    ]

