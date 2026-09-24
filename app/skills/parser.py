"""Markdown parser for skills.md."""
import re
from typing import List, Dict, Optional
from app.models.schemas import SkillDefinition


class SkillsMarkdownParser:
    """Parses skills.md content into strongly-typed SkillDefinition objects."""

    @staticmethod
    def parse(markdown_text: str) -> List[SkillDefinition]:
        skills: List[SkillDefinition] = []
        
        # Find the "Available Skills" section
        available_skills_match = re.search(r"#\s+Available Skills\s*\n(.*?)(?=\n#\s+Skill Selection Rules|\Z)", markdown_text, re.DOTALL)
        if not available_skills_match:
            # Fallback to searching all ## numbered sections
            section_content = markdown_text
        else:
            section_content = available_skills_match.group(1)

        # Split by "## [number]. [Title]"
        skill_blocks = re.split(r"\n##\s+\d+\.\s+", "\n" + section_content)

        for block in skill_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.splitlines()
            name = lines[0].strip()

            # Extract Skill ID
            id_match = re.search(r"###\s+Skill ID\s*\n([^\n#]+)", block)
            skill_id = id_match.group(1).strip() if id_match else name.lower().replace(" ", "_")

            # Extract Description
            desc_match = re.search(r"###\s+Description\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            # Extract When to Use
            when_match = re.search(r"###\s+When to Use\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL)
            when_to_use = []
            if when_match:
                when_text = when_match.group(1).strip()
                when_to_use = [
                    re.sub(r"^[-*]\s*", "", line).strip()
                    for line in when_text.splitlines()
                    if line.strip().startswith(("-", "*"))
                ]

            # Extract Input
            input_match = re.search(r"###\s+Input\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL)
            input_spec = input_match.group(1).strip() if input_match else ""

            # Extract Output
            output_match = re.search(r"###\s+Output\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL)
            output_spec = []
            if output_match:
                output_text = output_match.group(1).strip()
                output_spec = [
                    re.sub(r"^\d+\.\s*", "", line).strip()
                    for line in output_text.splitlines()
                    if re.match(r"^\d+\.\s*", line.strip())
                ]

            # Extract Constraints
            constraints_match = re.search(r"###\s+Constraints\s*\n(.*?)(?=\n###|\n---|\Z)", block, re.DOTALL)
            constraints = []
            if constraints_match:
                constraints_text = constraints_match.group(1).strip()
                constraints = [
                    re.sub(r"^[-*]\s*", "", line).strip()
                    for line in constraints_text.splitlines()
                    if line.strip().startswith(("-", "*")) and not line.strip().startswith(("---", "***"))
                ]

            skill = SkillDefinition(
                id=skill_id,
                name=name,
                description=description,
                when_to_use=when_to_use,
                input_spec=input_spec,
                output_spec=output_spec,
                constraints=constraints,
            )
            skills.append(skill)

        return skills
