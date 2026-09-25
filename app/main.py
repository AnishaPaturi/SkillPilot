"""FastAPI entrypoint for SkillPilot."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from app.models.schemas import ChatRequest, ChatResponse, SkillDefinition
from app.skills.registry import SkillRegistry
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
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SkillPilot Agent Runtime",
        "version": "1.0.0",
        "registered_skills": len(registry.list_skills()),
    }


@app.get("/api/skills", response_model=List[SkillDefinition])
def get_skills():
    """Returns all currently registered skills parsed from skills.md."""
    return registry.list_skills()


@app.post("/api/skills/reload")
def reload_skills():
    """Dynamically reloads skills.md without restarting the server."""
    try:
        registry.reload()
        return {
            "status": "success",
            "message": "skills.md reloaded successfully",
            "total_skills": len(registry.list_skills()),
            "skills": [s.id for s in registry.list_skills()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload skills: {str(e)}")


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


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
