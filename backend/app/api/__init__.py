"""API route aggregation."""

from fastapi import APIRouter

from app.api import agents, auth, feedback, models, skills, tools

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(agents.router)
api_router.include_router(auth.router)
api_router.include_router(feedback.router)
api_router.include_router(models.router)
api_router.include_router(skills.router)
api_router.include_router(tools.router)

__all__ = ["api_router"]