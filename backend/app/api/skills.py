"""Skill API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.api.deps import Storage, UserId
from app.application.skill_service import SkillService
from app.domain.skill import Skill
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skills", tags=["skills"])


class CreateSkillRequest(BaseModel):
    name: str = Field(max_length=64)
    description: str = Field(max_length=1024, default="")
    path: str = Field(max_length=500, default="")


class UpdateSkillRequest(BaseModel):
    name: Optional[str] = Field(max_length=64, default=None)
    description: Optional[str] = Field(max_length=1024, default=None)
    status: Optional[str] = Field(default=None)


@router.post("", response_model=Skill)
async def create_skill(
    request: CreateSkillRequest,
    storage: Storage,
    user_id: UserId,
) -> Skill:
    """Create a new skill."""
    skill = Skill(
        name=request.name,
        description=request.description,
        path=request.path,
        user_id=user_id,
    )
    service = SkillService(storage)
    return await service.create(skill)


@router.get("", response_model=List[Skill])
async def list_skills(
    storage: Storage,
    user_id: UserId,
    offset: int = 0,
    limit: int = 100,
) -> List[Skill]:
    """List skills for current user."""
    service = SkillService(storage)
    return await service.list_by_user(user_id, offset, limit)


@router.get("/{skill_id}", response_model=Skill)
async def get_skill(
    skill_id: str,
    storage: Storage,
) -> Skill:
    """Get skill by ID."""
    service = SkillService(storage)
    skill = await service.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    storage: Storage,
) -> Skill:
    """Update skill."""
    service = SkillService(storage)
    data = request.model_dump(exclude_unset=True)
    skill = await service.update(skill_id, data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    storage: Storage,
) -> dict:
    """Delete skill."""
    service = SkillService(storage)
    deleted = await service.delete(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"ok": True}


@router.get("/{skill_id}/files")
async def list_skill_files(
    skill_id: str,
    storage: Storage,
) -> List[str]:
    """List skill files."""
    service = SkillService(storage)
    return await service.list_files(skill_id)


@router.get("/{skill_id}/files/{filename}")
async def get_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
) -> Response:
    """Get skill file content."""
    service = SkillService(storage)
    content = await service.get_file(skill_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=content, media_type="application/octet-stream")


@router.put("/{skill_id}/files/{filename}")
async def save_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
    file: UploadFile = File(...),
) -> dict:
    """Save skill file via multipart upload."""
    service = SkillService(storage)
    content = await file.read()
    await service.save_file(skill_id, filename, content)
    return {"ok": True}


class SaveFileRequest(BaseModel):
    content: str


@router.put("/{skill_id}/files/{filename}/content")
async def save_skill_file_content(
    skill_id: str,
    filename: str,
    request: SaveFileRequest,
    storage: Storage,
) -> dict:
    """Save skill file content via JSON body."""
    service = SkillService(storage)
    await service.save_file(skill_id, filename, request.content.encode("utf-8"))
    return {"ok": True}


@router.delete("/{skill_id}/files/{filename}")
async def delete_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
) -> dict:
    """Delete skill file."""
    service = SkillService(storage)
    await service.delete_file(skill_id, filename)
    return {"ok": True}


class GenerateSkillRequest(BaseModel):
    name: str = Field(max_length=64)
    description: str = Field(max_length=1024)


# Path to the skill-creator skill
SKILL_CREATOR_PATH = "/Users/wilde/Downloads/skills-main/skills/skill-creator"
SKILL_CREATOR_SKILL_PATH = f"{SKILL_CREATOR_PATH}/SKILL.md"

# Read the skill-creator SKILL.md content at module load time
import pathlib
SKILL_CREATOR_CONTENT = pathlib.Path(SKILL_CREATOR_SKILL_PATH).read_text(encoding="utf-8")


@router.post("/generate")
async def generate_skill(
    request: GenerateSkillRequest,
    storage: Storage,
    user_id: UserId,
):
    """Generate a new skill using AI.

    Creates a skill entity and uses the skill-creator skill
    to generate the skill code based on the description.
    """
    import json
    import re
    from datetime import datetime, timezone
    from fastapi.responses import StreamingResponse
    from app.domain.agent import Agent
    from app.domain.base import EntityId
    from app.deepagents.wrapper import DeepAgentsRunner

    # Create skill entity
    skill_id = str(EntityId.generate())
    skill = Skill(
        id=EntityId(skill_id),
        name=request.name,
        description=request.description,
        path=f"/skills/{skill_id}/",
        user_id=user_id,
    )
    await storage.save_skill(skill)

    # Build system prompt that includes the full skill-creator instructions
    system_prompt = (
        f"You are a skill creator. Use the following skill-creator skill instructions to create a new skill.\n\n"
        f"=== SKILL-CREATOR SKILL ===\n"
        f"{SKILL_CREATOR_CONTENT}\n"
        f"=== END SKILL-CREATOR SKILL ===\n\n"
        f"User wants a skill called \"{request.name}\" with description: {request.description}\n\n"
        f'Output the skill files as JSON with this format:\n'
        f'{{"name": "{request.name}", "description": "{request.description}", "files": [{{"filename": "SKILL.md", "content": "# skill content"}}, {{"filename": "scripts/script.py", "content": "# script content"}}]}}\n\n'
        f"Only respond with valid JSON, no other text."
    )

    # Create a minimal agent for running with skill-creator skill
    agent = Agent(
        id=EntityId("skill-creator-agent"),
        name="Skill Creator",
        description="An agent that creates new skills",
        role="skill creator",
        goal=request.description,
        backstory="",
        skill_ids=[],
        tool_ids=[],
        model_config_id=None,
        user_id=user_id,
    )

    runner = DeepAgentsRunner(agent, storage, system_prompt_override=system_prompt)

    async def stream_events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'skill_id': skill_id})}\n\n"

            # Collect all response chunks to get the full JSON
            full_response = ""
            await runner.create()

            async for chunk in runner.run(f"Create a skill called '{request.name}' that does: {request.description}"):
                if chunk:
                    content = chunk.replace("<think>", "").replace("", "")
                    if content.strip():
                        full_response += content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'skill_id': skill_id})}\n\n"

            # Parse the JSON response and save the files
            try:
                # Find the JSON object - find the first '{' outside of strings
                json_start = -1
                in_string = False
                escape_next = False
                for i, char in enumerate(full_response):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if char == '{':
                        json_start = i
                        break

                if json_start == -1:
                    raise ValueError("No JSON found in response")

                # Find the matching closing brace by counting nesting level
                brace_count = 0
                in_string = False
                escape_next = False
                end_idx = -1

                for i in range(json_start, len(full_response)):
                    char = full_response[i]
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break

                if end_idx == -1:
                    raise ValueError("Could not find matching closing brace")

                json_str = full_response[json_start:end_idx]
                skill_data = json.loads(json_str)
                files = skill_data.get("files", [])
                for file_info in files:
                    filename = file_info.get("filename", "")
                    content = file_info.get("content", "")
                    if filename and content:
                        await storage.save_skill_file(skill_id, filename, content.encode("utf-8"))
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': f'Failed to save skill files: {str(e)}'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )