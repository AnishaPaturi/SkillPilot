"""Markdown parser for skills.md."""
import re
from typing import List, Dict, Optional, Any
from app.models.schemas import SkillDefinition


class SkillsMarkdownParser:
    """Parses skills.md content into strongly-typed SkillDefinition objects."""

    @staticmethod
    def parse(markdown_text: str) -> List[SkillDefinition]:
        if not markdown_text or not markdown_text.strip():
            return []

        skills: List[SkillDefinition] = []

        # Find the "Available Skills" section if present; otherwise inspect the whole document
        available_skills_match = re.search(
            r"#\s+Available Skills\s*\n(.*?)(?=\n#\s+Skill Selection Rules|\n#\s+Execution Rules|\Z)",
            markdown_text,
            re.DOTALL | re.IGNORECASE,
        )
        if available_skills_match:
            section_content = available_skills_match.group(1)
        else:
            section_content = markdown_text

        # Split by "## [optional number.] [Title]"
        # Matches "## 1. Skill Name", "## Skill Name", "## [Skill Name]"
        skill_blocks = re.split(r"\n##\s+", "\n" + section_content)

        for block in skill_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.splitlines()
            raw_title = lines[0].strip()

            # Ignore non-skill sections that might appear under ## (e.g. Overview, Rules, Error Handling)
            non_skill_titles = {
                "agent overview", "skill selection rules", "execution rules",
                "error handling", "response rules", "available skills", "overview"
            }
            clean_title = re.sub(r"^\d+\.\s*", "", raw_title).strip()
            if clean_title.lower() in non_skill_titles and "### Skill ID" not in block and "### Description" not in block:
                continue

            name = clean_title

            # Extract Skill ID
            id_match = re.search(r"###\s+Skill ID\s*\n([^\n#]+)", block, re.IGNORECASE)
            if not id_match:
                id_match = re.search(r"\*\*Skill ID:\*\*\s*`?([^\n`*]+)`?", block, re.IGNORECASE)

            if id_match:
                skill_id = id_match.group(1).strip()
            else:
                skill_id = re.sub(r"[^a-zA-Z0-9_]+", "_", name.lower()).strip("_")

            # Extract Description
            desc_match = re.search(r"###\s+Description\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL | re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r"\*\*Description:\*\*\s*(.*?)(?=\n\*\*|\n###|\Z)", block, re.DOTALL | re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""

            # Extract When to Use / Triggers
            when_match = re.search(r"###\s+(?:When to Use|Triggers|Usage Triggers)\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL | re.IGNORECASE)
            when_to_use = []
            if when_match:
                when_text = when_match.group(1).strip()
                when_to_use = [
                    re.sub(r"^[-*]\s*", "", line).strip().strip('"').strip("'")
                    for line in when_text.splitlines()
                    if line.strip().startswith(("-", "*")) and not line.strip().startswith(("---", "***"))
                ]

            # Extract Input
            input_match = re.search(r"###\s+(?:Input|Input Spec|Expected Input)\s*\n(.*?)(?=\n###|\Z)", block, re.DOTALL | re.IGNORECASE)
            input_spec = input_match.group(1).strip() if input_match else "User request"

            # Extract Output
            output_match = re.search(r"###\s+(?:Output|Output Spec|Output Requirements)\s*\n(.*?)(?=\n###|\n---|\Z)", block, re.DOTALL | re.IGNORECASE)
            output_spec = []
            if output_match:
                output_text = output_match.group(1).strip()
                for line in output_text.splitlines():
                    line_s = line.strip()
                    if re.match(r"^\d+\.\s*", line_s):
                        output_spec.append(re.sub(r"^\d+\.\s*", "", line_s).strip())
                    elif line_s.startswith(("-", "*")) and not line_s.startswith(("---", "***")):
                        output_spec.append(re.sub(r"^[-*]\s*", "", line_s).strip())

            # Extract Constraints
            constraints_match = re.search(r"###\s+(?:Constraints|Safety|Rules)\s*\n(.*?)(?=\n###|\n---|\Z)", block, re.DOTALL | re.IGNORECASE)
            constraints = []
            if constraints_match:
                constraints_text = constraints_match.group(1).strip()
                constraints = [
                    re.sub(r"^[-*]\s*", "", line).strip()
                    for line in constraints_text.splitlines()
                    if line.strip().startswith(("-", "*")) and not line.strip().startswith(("---", "***"))
                ]

            # Skip blocks that have neither description nor when_to_use nor output_spec
            if not description and not when_to_use and not output_spec:
                continue

            skill = SkillDefinition(
                id=skill_id,
                name=name or skill_id.replace("_", " ").title(),
                description=description or f"Skill for {name}",
                when_to_use=when_to_use,
                input_spec=input_spec,
                output_spec=output_spec if output_spec else ["Result"],
                constraints=constraints,
            )
            skills.append(skill)

        return skills

    @staticmethod
    def validate_markdown(markdown_text: str) -> Dict[str, Any]:
        """Parses markdown and returns diagnostic status, parsed skills, and any warnings."""
        if not markdown_text or not markdown_text.strip():
            return {
                "valid": False,
                "error": "The uploaded file is empty.",
                "warnings": [],
                "skills": [],
                "total_skills": 0,
            }

        try:
            skills = SkillsMarkdownParser.parse(markdown_text)
            if not skills:
                return {
                    "valid": False,
                    "error": (
                        "No skill definitions could be recognized. Please format skills with a '## [Skill Name]' "
                        "header and sections like '### Skill ID', '### Description', '### When to Use', and '### Output'."
                    ),
                    "warnings": [],
                    "skills": [],
                    "total_skills": 0,
                }

            seen_ids = set()
            duplicates = []
            warnings = []
            for s in skills:
                if s.id in seen_ids:
                    duplicates.append(s.id)
                seen_ids.add(s.id)
                if not s.when_to_use:
                    warnings.append(f"Skill '{s.name}' ({s.id}) has no trigger phrases under '### When to Use'.")
                if not s.output_spec:
                    warnings.append(f"Skill '{s.name}' ({s.id}) has no output specification items.")

            if duplicates:
                warnings.append(f"Duplicate skill IDs detected: {', '.join(duplicates)}")

            return {
                "valid": True,
                "error": None,
                "warnings": warnings,
                "skills": skills,
                "total_skills": len(skills),
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Parsing exception: {str(e)}",
                "warnings": [],
                "skills": [],
                "total_skills": 0,
            }
