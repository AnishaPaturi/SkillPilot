"""Validator module for verifying skill execution outputs against contracts."""
import re
from typing import List, Optional
from app.models.schemas import SkillDefinition, ValidationResult


class OutputValidator:
    """Validates generated outputs against the skill's defined output specifications and constraints."""

    @staticmethod
    def validate(skill: SkillDefinition, response_text: str) -> ValidationResult:
        if not response_text:
            return ValidationResult(is_valid=False, missing_elements=["Response is empty"], feedback="No content generated.")

        missing_elements: List[str] = []

        # Check if response addresses key output requirements
        resp_lower = response_text.lower()
        for item in skill.output_spec:
            # Check key keywords from the output specification item
            item_keywords = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", item)]
            # If at least one significant keyword is present, consider addressed
            found = any(k in resp_lower for k in item_keywords)
            if not found:
                missing_elements.append(item)

        # Check constraints
        feedback_notes = []
        if skill.id == "security_analysis":
            # Safety check: ensure no exploit payload instructions
            if "exploit payload" in resp_lower or "how to exploit" in resp_lower:
                feedback_notes.append("Warning: Output may violate defensive security constraints.")

        is_valid = len(missing_elements) <= 1  # Tolerant threshold for formatting variations

        return ValidationResult(
            is_valid=is_valid,
            missing_elements=missing_elements,
            feedback="; ".join(feedback_notes) if feedback_notes else None,
        )
