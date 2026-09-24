"""Skill Router for matching user intent to skills."""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
from app.skills.registry import SkillRegistry
from app.models.schemas import SkillDefinition


class SkillRouter:
    """Routes user requests to the most appropriate skill defined in skills.md."""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()

    def route(self, query: str, code: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
        """
        Determines the primary skill ID and any supporting skills for the query.
        Returns (primary_skill_id, supporting_skills).
        """
        # First check if LLM routing is available
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key and api_key != "your_openrouter_api_key_here":
            try:
                return self._route_with_llm(query, code)
            except Exception:
                # Fall back to heuristic matching if LLM call fails
                pass

        return self._route_heuristic(query, code)

    def _route_heuristic(self, query: str, code: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
        """Deterministic heuristic router based on triggers and descriptions from skills.md."""
        q_lower = query.lower()
        skills = self.registry.list_skills()
        scores: Dict[str, int] = {s.id: 0 for s in skills}

        for skill in skills:
            # Check exact skill ID match
            if skill.id in q_lower:
                scores[skill.id] = scores.get(skill.id, 0) + 10

            # Check triggers
            for trigger in skill.when_to_use:
                t_lower = trigger.lower()
                if t_lower in q_lower:
                    scores[skill.id] = scores.get(skill.id, 0) + 5
                else:
                    # Partial word overlap
                    words = [w for w in t_lower.split() if len(w) > 3]
                    for w in words:
                        if w in q_lower:
                            scores[skill.id] = scores.get(skill.id, 0) + 1

            # Check description keywords
            desc_words = [w for w in skill.description.lower().split() if len(w) > 4]
            for w in desc_words:
                if w in q_lower:
                    scores[skill.id] = scores.get(skill.id, 0) + 1

        # Sort skills by match score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_scores or sorted_scores[0][1] <= 1:
            return None, []

        primary_skill = sorted_scores[0][0]
        supporting_skills = [
            sid for sid, score in sorted_scores[1:] if score >= 3 and sid != primary_skill
        ]

        return primary_skill, supporting_skills

    def _route_with_llm(self, query: str, code: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
        """LLM-based intent routing using OpenRouter."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        model_name = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-001")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        api_key = os.getenv("OPENROUTER_API_KEY")

        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.0,
        )

        catalog = self.registry.get_skills_catalog_prompt()
        system_prompt = f"""You are the SkillPilot Router. Your job is to select the single best skill for the user's request.
{catalog}

Return a valid JSON object only with format:
{{
  "primary_skill": "skill_id_or_null",
  "supporting_skills": ["optional_skill_id"],
  "reasoning": "brief explanation"
}}
If none of the available skills match the user's request, set "primary_skill" to null.
Do not invent skills.
"""
        user_prompt = f"User Request: {query}\n"
        if code:
            user_prompt += f"Code Context:\n```\n{code[:500]}\n```"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            data = json.loads(content)
            return data.get("primary_skill"), data.get("supporting_skills", [])
        except Exception:
            return self._route_heuristic(query, code)
