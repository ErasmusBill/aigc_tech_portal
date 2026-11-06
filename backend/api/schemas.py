from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    organization_id: str
    email: EmailStr
    password: str = Field(min_length=1)

class UserPayload(BaseModel):
    id: str
    orgId: str | None = ""
    name: str
    email: str
    systemRole: str = "standard_user"
    positionId: str | None = ""
    status: str = "Active"
    mustReset: bool = False
    profile: dict[str, Any] = {}

class LoginResponse(BaseModel):
    token: str
    user: UserPayload
    expires_in_seconds: int = 43200

class WorkspaceStateIn(BaseModel):
    state: dict[str, Any]

class WorkspaceStateOut(BaseModel):
    revision: int
    state: dict[str, Any]

class RecordPage(BaseModel):
    rows: list[dict[str, Any]]
    total: int = 0
    limit: int
    offset: int
    page: int = 1
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    next_offset: int | None = None
    prev_offset: int | None = None

class UserPage(BaseModel):
    rows: list[UserPayload]
    total: int = 0
    limit: int
    offset: int
    page: int = 1
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    next_offset: int | None = None
    prev_offset: int | None = None

class FileItem(BaseModel):
    id: str
    owner_id: int | None = None
    organization_id: str = ""
    category: str = "general"
    original_name: str
    mime_type: str = ""
    size_bytes: int = 0
    sha256: str = ""
    classification: str = "Internal"
    download_url: str
    created_at: str

class FilePage(BaseModel):
    rows: list[FileItem]
    total: int = 0
    limit: int
    offset: int
    page: int = 1
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    next_offset: int | None = None
    prev_offset: int | None = None

class AttendancePage(BaseModel):
    rows: list[dict[str, Any]]
    total: int = 0
    limit: int
    offset: int
    page: int = 1
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    next_offset: int | None = None
    prev_offset: int | None = None

class AttendanceAction(BaseModel):
    event_type: Literal["CHECK_IN","BREAK_OUT","BREAK_IN","CLOCK_OUT"]
    occurred_at: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accuracy_m: float | None = None
    metadata: dict[str, Any] = {}

class InviteRequest(BaseModel):
    organization_id: str
    name: str
    email: EmailStr
    position_id: str = ""
    system_role: str = "standard_user"

class AIRequest(BaseModel):
    kind: str = "general"
    task: str
    context: str = ""
    output: str = "Professional narrative"

class ExportRequest(BaseModel):
    format: Literal["word","excel"] = "word"
    title: str
    content: str
    kind: str = "general"

class PasswordChangeRequest(BaseModel):
    current_password: str = ""
    new_password: str = Field(min_length=8, max_length=8, description="Password must be only 8 characters long")

class RecordIn(BaseModel):
    id: str
    orgId: str = ""
    country: str = ""
    userId: str = ""
    status: str = ""
    data: dict[str, Any] = {}
