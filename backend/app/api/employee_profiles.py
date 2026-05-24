"""Employee Profile API routes."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import Storage, UserId
from app.application.employee_profile_service import EmployeeProfileService
from app.domain.employee_profile import EmployeeProfile
from app.infrastructure.git_manager import GitManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employee-profiles", tags=["employee-profiles"])


# --- Pydantic schemas ---

class EmployeeProfileResponse(BaseModel):
    id: str
    name: str
    role: str = ""
    goal: str = ""
    backstory: str = ""
    personality: str = ""
    constraints: str = ""
    working_rules: str = ""
    status: str = "active"
    git_path: str = ""
    user_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EmployeeProfileSummaryResponse(BaseModel):
    id: str
    name: str
    role: str = ""
    goal: str = ""
    status: str = "active"
    git_path: str = ""


class CreateEmployeeProfile(BaseModel):
    name: str = Field(max_length=100)
    role: str = Field(default="", max_length=500)
    goal: str = Field(default="", max_length=1000)
    backstory: str = Field(default="", max_length=2000)
    personality: str = Field(default="", max_length=2000)
    constraints: str = Field(default="", max_length=2000)
    working_rules: str = Field(default="", max_length=2000)


class UpdateEmployeeProfile(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=500)
    goal: str | None = Field(default=None, max_length=1000)
    backstory: str | None = Field(default=None, max_length=2000)
    personality: str | None = Field(default=None, max_length=2000)
    constraints: str | None = Field(default=None, max_length=2000)
    working_rules: str | None = Field(default=None, max_length=2000)
    status: str | None = None


class UpdateFileContent(BaseModel):
    content: str


class FileListResponse(BaseModel):
    files: List[str]


class FileContentResponse(BaseModel):
    filename: str
    content: str


# --- Helper ---

def _service(storage) -> EmployeeProfileService:
    return EmployeeProfileService(storage, GitManager())


def _to_response(profile: EmployeeProfile) -> EmployeeProfileResponse:
    return EmployeeProfileResponse(
        id=str(profile.id),
        name=profile.name,
        role=profile.role,
        goal=profile.goal,
        backstory=profile.backstory,
        personality=profile.personality,
        constraints=profile.constraints,
        working_rules=profile.working_rules,
        status=profile.status,
        git_path=profile.git_path,
        user_id=str(profile.user_id) if profile.user_id else None,
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


def _to_summary(profile: EmployeeProfile) -> EmployeeProfileSummaryResponse:
    return EmployeeProfileSummaryResponse(
        id=str(profile.id),
        name=profile.name,
        role=profile.role,
        goal=profile.goal,
        status=profile.status,
        git_path=profile.git_path,
    )


# --- Routes ---

@router.post("", response_model=EmployeeProfileResponse)
async def create_employee_profile(
    data: CreateEmployeeProfile,
    storage: Storage,
    user_id: UserId,
) -> EmployeeProfileResponse:
    profile = EmployeeProfile(
        name=data.name,
        role=data.role,
        goal=data.goal,
        backstory=data.backstory,
        personality=data.personality,
        constraints=data.constraints,
        working_rules=data.working_rules,
        user_id=user_id,
    )
    service = _service(storage)
    created = await service.create(profile)
    return _to_response(created)


@router.get("", response_model=List[EmployeeProfileSummaryResponse])
async def list_employee_profiles(
    storage: Storage,
    user_id: UserId,
) -> List[EmployeeProfileSummaryResponse]:
    service = _service(storage)
    profiles = await service.list_by_user(user_id)
    return [_to_summary(p) for p in profiles]


@router.get("/{profile_id}", response_model=EmployeeProfileResponse)
async def get_employee_profile(
    profile_id: str,
    storage: Storage,
) -> EmployeeProfileResponse:
    service = _service(storage)
    profile = await service.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return _to_response(profile)


@router.put("/{profile_id}", response_model=EmployeeProfileResponse)
async def update_employee_profile(
    profile_id: str,
    data: UpdateEmployeeProfile,
    storage: Storage,
) -> EmployeeProfileResponse:
    service = _service(storage)
    profile = await service.update(profile_id, data.model_dump(exclude_unset=True))
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return _to_response(profile)


@router.delete("/{profile_id}")
async def delete_employee_profile(
    profile_id: str,
    storage: Storage,
) -> dict:
    service = _service(storage)
    deleted = await service.delete(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return {"deleted": True}


@router.get("/{profile_id}/files", response_model=FileListResponse)
async def list_profile_files(
    profile_id: str,
    storage: Storage,
) -> FileListResponse:
    service = _service(storage)
    files = await service.list_files(profile_id)
    return FileListResponse(files=files)


@router.get("/{profile_id}/files/{filename}", response_model=FileContentResponse)
async def get_profile_file(
    profile_id: str,
    filename: str,
    storage: Storage,
) -> FileContentResponse:
    service = _service(storage)
    file_data = await service.get_file(profile_id, filename)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    return FileContentResponse(**file_data)


@router.put("/{profile_id}/files/{filename}/content")
async def update_profile_file(
    profile_id: str,
    filename: str,
    data: UpdateFileContent,
    storage: Storage,
) -> dict:
    service = _service(storage)
    updated = await service.update_file(profile_id, filename, data.content)
    if not updated:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"updated": True}


class GitLogResponse(BaseModel):
    hash: str
    message: str
    date: str


@router.get("/{profile_id}/git-log", response_model=List[GitLogResponse])
async def get_employee_profile_git_log(
    profile_id: str,
    storage: Storage,
) -> List[GitLogResponse]:
    service = _service(storage)
    log_entries = await service.get_git_log(profile_id)
    return [GitLogResponse(hash=e["hash"], message=e["message"], date=e["date"]) for e in log_entries]
