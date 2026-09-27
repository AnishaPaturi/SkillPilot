"""FastAPI entrypoint for SkillPilot."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from app.models.schemas import ChatRequest, ChatResponse, SkillDefinition, SkillUploadRequest
from app.skills.registry import SkillRegistry
from app.skills.parser import SkillsMarkdownParser
from app.agent.graph import SkillPilotAgent

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SkillPilot API",
    description="Skill-driven autonomous AI agent with dynamic markdown capability configuration.",
    version="1.0.0",
)

# Enable CORS for local Streamlit or web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global registry and agent instances
skills_path = os.getenv("SKILLS_FILE_PATH", "skills.md")
registry = SkillRegistry()
agent = SkillPilotAgent(registry=registry)


@app.get("/")
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SkillPilot Agent Runtime",
        "version": "1.0.0",
        "registered_skills": len(registry.list_skills()),
        "is_custom_skills": registry.is_custom,
        "active_source": registry.active_source,
    }


@app.get("/api/skills", response_model=List[SkillDefinition])
def get_skills():
    """Returns all currently registered skills parsed from skills.md or custom upload."""
    return registry.list_skills()


@app.post("/api/skills/reload")
def reload_skills():
    """Dynamically reloads default skills.md without restarting the server."""
    global agent
    try:
        registry.reload()
        agent = SkillPilotAgent(registry=registry)
        return {
            "status": "success",
            "message": "skills.md reloaded successfully",
            "total_skills": len(registry.list_skills()),
            "skills": [s.id for s in registry.list_skills()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload skills: {str(e)}")


@app.post("/api/skills/upload")
def upload_skills(request: SkillUploadRequest):
    """Uploads, parses, and activates a custom skills markdown definition."""
    global agent
    validation = SkillsMarkdownParser.validate_markdown(request.content)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    try:
        loaded = registry.load_from_content(request.content, source_name=request.filename or "uploaded_skills.md")
        agent = SkillPilotAgent(registry=registry)
        return {
            "status": "success",
            "message": f"Successfully parsed and activated {len(loaded)} skills from {request.filename or 'uploaded markdown'}",
            "total_skills": len(loaded),
            "warnings": validation.get("warnings", []),
            "skills": [s.id for s in loaded],
            "skills_catalog": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "triggers": s.when_to_use,
                    "input_spec": s.input_spec,
                    "output_spec": s.output_spec,
                    "constraints": s.constraints,
                }
                for s in loaded
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate custom skills: {str(e)}")


@app.post("/api/skills/reset")
def reset_skills():
    """Restores the default built-in skills.md specification."""
    global agent
    try:
        registry.reset_to_default()
        agent = SkillPilotAgent(registry=registry)
        return {
            "status": "success",
            "message": "Reset to default built-in skills.md catalog successfully",
            "total_skills": len(registry.list_skills()),
            "skills": [s.id for s in registry.list_skills()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset skills: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Processes a user request through the skill-driven agent pipeline."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        response = agent.run(
            query=request.query,
            code=request.code,
            session_id=request.session_id,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")


@app.post("/api/chain/plan")
def plan_chain(request: ChatRequest):
    """Detects and returns the ordered multi-step skill chain for a given request."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chain = agent.router.plan_chain(request.query, request.code)
    return {
        "query": request.query,
        "skill_chain": chain,
        "is_chained": len(chain) > 1,
        "total_steps": len(chain),
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
