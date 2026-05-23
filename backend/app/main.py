"""FastAPI application entry point."""

import logging
import sys

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, auth, skills, tools, models, feedback, scheduled_tasks, logs, sessions, conversation_memories
from app.api.deps import get_current_user
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
)

# CORS middleware — use explicit allowed origins from config
allowed_origins = getattr(settings.app, "allowed_origins", None)
if not allowed_origins:
    # Default to localhost origins for development
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_auth():
    """Dependency that requires authentication.

    Applied as a default dependency to all routers via include_router().
    """
    return Depends(get_current_user)


# Include routers with global auth dependency
# Auth routes are exempt — they handle login/register themselves
app.include_router(auth.router, prefix="/api")
app.include_router(agents.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(skills.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(tools.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(models.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(feedback.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(scheduled_tasks.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(logs.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(sessions.router, prefix="/api", dependencies=[_require_auth()])
app.include_router(conversation_memories.router, prefix="/api", dependencies=[_require_auth()])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
