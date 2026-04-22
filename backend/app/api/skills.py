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
    """Save skill file."""
    service = SkillService(storage)
    content = await file.read()
    await service.save_file(skill_id, filename, content)
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