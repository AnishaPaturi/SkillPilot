"""Skill Router for matching user intent to skills."""
import os
import json
import re
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

        q_tokens = set(re.findall(r"\b[a-z]{3,}\b", q_lower))
        STOP_WORDS = {
            "this", "that", "what", "which", "with", "from", "your", "have", "been",
            "will", "would", "could", "should", "does", "about", "line", "work",
            "make", "user", "when", "asks", "for", "and", "the", "how", "into",
            "some", "more", "such", "like", "give"
        }

        DISTINCTIVE_ANCHORS = {
            "security_analysis": ["secur", "vulnerab", "secret", "credential", "auth", "inject"],
            "code_explanation": ["explain", "line by line", "how does", "what does", "how it works", "walkthrough"],
            "documentation": ["document", "readme", "api doc", "technical doc", "setup instruction"],
            "task_planning": ["plan", "phase", "step", "how to build", "how to implement", "architect", "break down"],
            "code_analysis": ["bug", "improv", "inefficien", "refactor", "code quality", "smell", "review"],
        }

        for skill_id, anchors in DISTINCTIVE_ANCHORS.items():
            if skill_id in scores and any(anchor in q_lower for anchor in anchors):
                scores[skill_id] += 15

        for skill in skills:
            # Check exact skill ID match
            if skill.id in q_lower:
                scores[skill.id] = scores.get(skill.id, 0) + 12

            # Boost on distinctive ID parts (e.g., 'security', 'documentation', 'planning')
            for part in skill.id.split("_"):
                if part in q_tokens and part not in STOP_WORDS and part not in {"code", "analysis"}:
                    scores[skill.id] = scores.get(skill.id, 0) + 8

            # Check triggers
            for trigger in skill.when_to_use:
                t_lower = trigger.lower()
                if t_lower in q_lower:
                    scores[skill.id] = scores.get(skill.id, 0) + 8
                else:
                    # Meaningful word tokens overlap
                    t_tokens = [w for w in re.findall(r"\b[a-z]{3,}\b", t_lower) if w not in STOP_WORDS]
                    for w in t_tokens:
                        if w in q_tokens:
                            scores[skill.id] = scores.get(skill.id, 0) + 3

            # Check description keywords
            desc_words = [w for w in re.findall(r"\b[a-z]{4,}\b", skill.description.lower()) if w not in STOP_WORDS]
            for w in desc_words:
                if w in q_tokens:
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

    def route_intent(self, query: str, code: Optional[str] = None) -> Dict[str, Any]:
        """
        Phase 3 Structured Router: returns structured decision with confidence score.
        Example: {"skill": "code_analysis", "confidence": 0.94}
        """
        primary_skill, supporting = self.route(query, code)
        if not primary_skill:
            return {
                "skill": None,
                "confidence": 0.0,
                "supporting_skills": [],
                "message": "I don't currently have a skill that matches this request."
            }

        # Calculate normalized confidence
        q_lower = query.lower()
        skill = self.registry.get_skill(primary_skill)
        confidence = 0.85
        if skill and any(t.lower() in q_lower for t in skill.when_to_use):
            confidence = 0.95
        elif primary_skill in q_lower:
            confidence = 0.98

        return {
            "skill": primary_skill,
            "confidence": round(confidence, 2),
            "supporting_skills": supporting,
        }

    def plan_chain(self, query: str, code: Optional[str] = None) -> List[str]:
        """
        Phase 6 Skill Chaining:
        Detects if the request requires an ordered multi-step sequence of skills.
        Example:
            "Analyze this Python API for security issues and then create documentation explaining the vulnerabilities."
            -> ["security_analysis", "documentation"]
        """
        q_lower = query.lower()

        # Split on sequential conjunctions: 'and then', 'then', 'followed by', 'after that'
        split_pattern = r"\b(?:and\s+then|followed\s+by|after\s+that|then)\b"
        segments = re.split(split_pattern, q_lower)

        chain: List[str] = []
        if len(segments) > 1:
            for seg in segments:
                seg_clean = seg.strip()
                if not seg_clean:
                    continue
                skill_id, _ = self.route(seg_clean, code)
                if skill_id and (not chain or chain[-1] != skill_id):
                    chain.append(skill_id)

        # Fallback to single primary skill if no chain markers found
        if not chain:
            primary_skill, _ = self.route(query, code)
            if primary_skill:
                chain = [primary_skill]

        return chain


