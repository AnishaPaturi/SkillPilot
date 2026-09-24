"""Task Planning Tool: Breaks complex technical requirements into executable plans."""
import re
from typing import Dict, Any, List


class TaskPlannerTool:
    """
    Task Planning Tool
    Input  → requirement
    Output → implementation plan (Goal, Requirements, Implementation phases, Tasks, Dependencies, Testing strategy)
    """

    @classmethod
    def plan(cls, requirement: str) -> Dict[str, Any]:
        """Generates a structured implementation plan from a technical requirement."""
        req_clean = requirement.strip()

        # 1. Goal
        goal = f"Successfully implement and deploy: '{req_clean}'."

        # 2. Requirements Analysis
        req_lower = req_clean.lower()
        functional_reqs: List[str] = [
            f"Deliver core functionality specified by: {req_clean}.",
            "Provide clean, documented interfaces and error-handling paths.",
        ]

        if any(w in req_lower for w in ["api", "endpoint", "rest", "backend"]):
            functional_reqs.append("Expose structured REST/HTTP endpoints with request validation.")
        if any(w in req_lower for w in ["auth", "login", "jwt", "token"]):
            functional_reqs.append("Implement secure authentication and role-based access control.")
        if any(w in req_lower for w in ["database", "sql", "storage", "cache", "redis"]):
            functional_reqs.append("Establish persistent data schemas and connection pooling.")

        non_functional_reqs = [
            "Maintain high test coverage with automated unit and integration tests.",
            "Ensure low latency, modular maintainability, and clean separation of concerns.",
            "Enforce defensive security practices and secret isolation.",
        ]

        # 3 & 4. Implementation Phases & Tasks
        phases = [
            {
                "phase": "Phase 1: Architecture & Project Scaffolding",
                "tasks": [
                    "Define system boundaries, component diagrams, and interface contracts.",
                    "Initialize repository, virtual environment, and dependency manifests.",
                    "Set up configuration management and environment variables (.env).",
                ],
                "deliverables": "Scaffolded repository with dependency baseline.",
            },
            {
                "phase": "Phase 2: Core Domain Logic Implementation",
                "tasks": [
                    f"Implement primary business logic models addressing: '{req_clean[:80]}...'.",
                    "Add domain validation and custom exception hierarchies.",
                    "Develop unit tests for core computational paths.",
                ],
                "deliverables": "Tested core domain engine.",
            },
            {
                "phase": "Phase 3: Integration, APIs & Interfaces",
                "tasks": [
                    "Implement API controllers / CLI entrypoints connecting to domain logic.",
                    "Wire data persistence, caching, or external service clients.",
                    "Integrate request/response logging and operational middleware.",
                ],
                "deliverables": "Fully wired, callable application interfaces.",
            },
            {
                "phase": "Phase 4: Verification, Hardening & Deployment",
                "tasks": [
                    "Execute integration tests, boundary tests, and security scans.",
                    "Benchmark performance under anticipated load conditions.",
                    "Author developer documentation, README, and deployment guides.",
                ],
                "deliverables": "Production-ready, verified release.",
            },
        ]

        # 5. Dependencies
        dependencies = [
            "Python 3.11+",
            "Modern dependency manager (uv or pip)",
            "Testing suite (pytest, pytest-asyncio)",
            "Data validation framework (Pydantic)",
        ]
        if "fastapi" in req_lower or "api" in req_lower:
            dependencies.append("FastAPI + Uvicorn")
        if "sql" in req_lower or "database" in req_lower:
            dependencies.append("SQLAlchemy / SQL Database Driver")
        if "redis" in req_lower:
            dependencies.append("Redis-py Client")

        # 6. Testing Strategy
        testing_strategy = (
            "1. Unit Tests: Verify isolated functions, data transformations, and validation rules.\n"
            "2. Integration Tests: Validate end-to-end API workflows and component interop.\n"
            "3. Security & Quality Gate: Run static analysis and vulnerability scans before deployment."
        )

        # Formatted Markdown
        phases_md = []
        for p in phases:
            phases_md.append(f"#### {p['phase']}")
            for t in p["tasks"]:
                phases_md.append(f"- [ ] {t}")
            phases_md.append(f"*Deliverable:* {p['deliverables']}\n")

        markdown_plan = f"""# Implementation Plan

## 1. Goal
{goal}

## 2. Requirements
### Functional:
{chr(10).join(f"- {r}" for r in functional_reqs)}

### Non-Functional:
{chr(10).join(f"- {r}" for r in non_functional_reqs)}

## 3. Implementation Phases & 4. Tasks
{chr(10).join(phases_md)}

## 5. Dependencies
{chr(10).join(f"- {d}" for d in dependencies)}

## 6. Testing Strategy
{testing_strategy}
"""

        return {
            "goal": goal,
            "requirements": {
                "functional": functional_reqs,
                "non_functional": non_functional_reqs,
            },
            "implementation_phases": phases,
            "dependencies": dependencies,
            "testing_strategy": testing_strategy,
            "markdown_plan": markdown_plan,
        }
