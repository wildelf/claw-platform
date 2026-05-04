"""Skill API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.api.deps import Storage, UserId
from app.application.skill_service import SkillService
from app.config import settings
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
    # Replace encoded slashes - FastAPI already decodes, but if the path
    # was split we need to reconstruct
    actual_filename = filename.replace('_SLASH_', '/')
    service = SkillService(storage)
    content = await service.get_file(skill_id, actual_filename)
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
    name: str = Field(max_length=64, description="Skill name")
    description: str = Field(max_length=1024, description="Skill description")
    prompt: str | None = Field(default=None, description="Optional prompt/instruction for generation")
    config: dict | None = Field(default=None, description="Optional config overrides")


class ExecuteSkillRequest(BaseModel):
    task: str = Field(max_length=5000, description="Task to execute with the skill")
    model_config_id: str | None = Field(default=None, description="Model config ID to use")


@router.post("/{skill_id}/execute")
async def execute_skill(
    skill_id: str,
    request: ExecuteSkillRequest,
    storage: Storage,
    user_id: UserId,
):
    """Execute a skill with a given task.

    Creates a minimal agent with just the target skill and runs
    the task through deepagents, streaming results back.
    """
    import logging
    import json
    logger = logging.getLogger(__name__)
    from fastapi.responses import StreamingResponse
    from app.domain.agent import Agent
    from app.domain.base import EntityId
    from app.deepagents.wrapper import DeepAgentsRunner

    # Get the skill
    logger.info(f"execute_skill called with skill_id={skill_id}")
    skill = await storage.get_skill(skill_id)
    if not skill:
        logger.warning(f"execute_skill: skill {skill_id} not found in storage")
        raise HTTPException(status_code=404, detail="Skill not found")
    logger.info(f"execute_skill: found skill {skill.name}")

    # Get skill files to include in context (for system prompt only, not backstory)
    skill_files = await storage.list_skill_files(skill_id)
    skill_summary = ", ".join(f"'{f}'" for f in skill_files) if skill_files else "SKILL.md"
    logger.info(f"execute_skill: skill files = {skill_files}")

    # Create a minimal agent for running the skill
    agent = Agent(
        id=EntityId(f"skill-exec-{skill_id}"),
        name=f"Skill Executor: {skill.name}",
        description=f"Executes the {skill.name} skill",
        role="skill executor",
        goal=request.task,
        backstory=f"This agent executes the '{skill.name}' skill. Skill files: {skill_summary}. The agent will read the SKILL.md file to understand how to execute the task.",
        skill_ids=[EntityId(skill_id)],
        tool_ids=[],
        text_model_config_id=EntityId(request.model_config_id) if request.model_config_id else None,
        user_id=user_id,
    )

    # Override system prompt to emphasize skill execution
    system_prompt = (
        f"You are executing the '{skill.name}' skill. "
        f"Read and follow the SKILL.md file carefully to complete the task. "
        f"The skill description is: {skill.description}"
    )

    logger.info(f"execute_skill: agent.skill_ids = {agent.skill_ids}")
    logger.info(f"execute_skill: system_prompt = {system_prompt[:200]}...")

    runner = DeepAgentsRunner(
        agent,
        storage,
        system_prompt_override=system_prompt,
    )

    async def stream_events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'skill_id': skill_id, 'task': request.task})}\n\n"

            await runner.create()

            async for event in runner.run(request.task):
                event_type = event.get("type", "content")
                logger.info(f"Skill execution event: {event_type} - {str(event)[:200]}")
                if event_type == "content":
                    content = event.get("content", "")
                    content = content.replace("<think>", "").replace("", "")
                    if content.strip():
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif event_type == "skill_reading":
                    yield f"data: {json.dumps({'type': 'skill_reading', 'file': event.get('file', '')})}\n\n"
                elif event_type == "tool_call":
                    tool_name = event.get("tool", "unknown")
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name})}\n\n"
                elif event_type == "thinking":
                    yield f"data: {json.dumps({'type': 'thinking', 'message': event.get('message', '')})}\n\n"
                elif event_type == "preparing":
                    yield f"data: {json.dumps({'type': 'preparing', 'message': event.get('message', '')})}\n\n"
                else:
                    try:
                        yield f"data: {json.dumps(event)}\n\n"
                    except (TypeError, ValueError):
                        pass

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Error in skill execution")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


SKILL_CREATOR_PATH = settings.skill_creator.path
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

    runner = DeepAgentsRunner(
        agent, storage,
        system_prompt_override=system_prompt,
        extra_skill_paths=[SKILL_CREATOR_PATH],
    )

    async def stream_events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'skill_id': skill_id})}\n\n"

            # Collect all response chunks to get the full JSON
            full_response = ""
            await runner.create()

            async for event in runner.run(f"Create a skill called '{request.name}' that does: {request.description}"):
                # Handle both dict events (messages mode) and string chunks
                if isinstance(event, dict):
                    content = event.get("content", "")
                elif isinstance(event, str):
                    content = event
                else:
                    continue
                if content:
                    content = content.replace("<think>", "").replace("</think>", "")
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
                        # Emit file event so frontend can display file tabs
                        yield f"data: {json.dumps({'type': 'file', 'filename': filename, 'content': content})}\n\n"
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