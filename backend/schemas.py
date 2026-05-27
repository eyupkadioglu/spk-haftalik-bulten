from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Department ────────────────────────────────────────────────────────────────
class DepartmentCreate(BaseModel):
    name: str
    code: Optional[str] = None
    organization_id: Optional[str] = None

class DepartmentOut(BaseModel):
    id: str
    name: str
    code: Optional[str]
    organization_id: Optional[str]
    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role_code: str
    department_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role_code: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: str
    name: str
    username: str
    role_code: str
    department_id: Optional[str]
    is_active: bool
    model_config = {"from_attributes": True}


# ── Bulletin ──────────────────────────────────────────────────────────────────
class BulletinCreate(BaseModel):
    year: int
    week_number: int
    title: Optional[str] = None

class BulletinUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

class BulletinOut(BaseModel):
    id: str
    year: int
    week_number: int
    title: Optional[str]
    status: str
    created_by: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Section ───────────────────────────────────────────────────────────────────
class SectionCreate(BaseModel):
    bulletin_id: str
    department_id: Optional[str] = None
    heading_group_code: Optional[str] = None
    heading_sub_group_code: Optional[str] = None

class SectionUpdate(BaseModel):
    heading_group_code: Optional[str] = None
    heading_sub_group_code: Optional[str] = None
    content_html: Optional[str] = None
    structured_tables: Optional[Any] = None
    tables: Optional[Any] = None
    no_content: Optional[bool] = None
    assigned_db_id: Optional[str] = None
    assigned_dby_id: Optional[str] = None

class SectionOut(BaseModel):
    id: str
    bulletin_id: str
    department_id: Optional[str]
    heading_group_code: Optional[str]
    heading_sub_group_code: Optional[str]
    status: str
    no_content: bool
    content_html: Optional[str]
    structured_tables: Optional[Any]
    tables: Optional[Any]
    assigned_db_id: Optional[str]
    assigned_dby_id: Optional[str]
    model_config = {"from_attributes": True}


# ── Entry ─────────────────────────────────────────────────────────────────────
class EntryCreate(BaseModel):
    content_html: Optional[str] = None
    structured_tables: Optional[Any] = None
    tables: Optional[Any] = None
    order: int = 1
    heading_group_code: Optional[str] = None
    heading_sub_group_code: Optional[str] = None

class EntryUpdate(BaseModel):
    content_html: Optional[str] = None
    structured_tables: Optional[Any] = None
    tables: Optional[Any] = None
    order: Optional[int] = None
    heading_group_code: Optional[str] = None
    heading_sub_group_code: Optional[str] = None
    approval_status: Optional[str] = None

class EntryOut(BaseModel):
    id: str
    section_id: str
    content_html: Optional[str]
    structured_tables: Optional[Any]
    tables: Optional[Any]
    order: int
    heading_group_code: Optional[str]
    heading_sub_group_code: Optional[str]
    approval_status: str
    created_by: Optional[str]
    created_by_role: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Log ───────────────────────────────────────────────────────────────────────
class LogOut(BaseModel):
    id: str
    action: str
    user_id: Optional[str]
    user_name: Optional[str]
    user_role: Optional[str]
    bulletin_id: Optional[str]
    section_id: Optional[str]
    entry_id: Optional[str]
    old_value: Optional[str]
    new_value_summary: Optional[str]
    reason: Optional[str]
    timestamp: datetime
    model_config = {"from_attributes": True}


# ── Archive ───────────────────────────────────────────────────────────────────
class ArchiveOut(BaseModel):
    id: str
    bulletin_id: str
    year: int
    week_number: int
    clean_html: Optional[str]
    logged_html: Optional[str]
    published_at: datetime
    approved_by_chair: Optional[str]
    model_config = {"from_attributes": True}
