"""In-memory registry for indexed skills."""
from typing import Dict, List, Optional
from app.models.schemas import SkillDefinition
from app.skills.loader import SkillLoader


class SkillRegistry:
    """Manages active skills in memory, providing fast lookup and catalog summaries."""

    def __init__(self, loader: Optional[SkillLoader] = None):
        self.loader = loader or SkillLoader()
        self._skills: Dict[str, SkillDefinition] = {}
        self.reload()

    def reload(self) -> None:
        """Reloads skills from the loader."""
        skills_list = self.loader.load_skills()
        self._skills = {skill.id: skill for skill in skills_list}

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Retrieves a skill definition by its ID."""
        return self._skills.get(skill_id)

    def list_skills(self) -> List[SkillDefinition]:
        """Returns all registered skills."""
        return list(self._skills.values())

    def get_skills_catalog_prompt(self) -> str:
        """Formats the list of available skills into a concise catalog prompt for the router."""
        catalog_lines = ["Available Skills:"]
        for skill in self._skills.values():
            triggers = ", ".join(f'"{t}"' for t in skill.when_to_use[:4])
            catalog_lines.append(f"- ID: {skill.id}")
            catalog_lines.append(f"  Name: {skill.name}")
            catalog_lines.append(f"  Description: {skill.description}")
            if triggers:
                catalog_lines.append(f"  Triggers: {triggers}")
        return "\n".join(catalog_lines)
