from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.types import JSON
from datetime import datetime
import uuid
from database import Base


def new_id() -> str:
    return uuid.uuid4().hex[:16]


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String(50), primary_key=True, default=new_id)
    name = Column(String(200), nullable=False)


class Department(Base):
    __tablename__ = "departments"
    id = Column(String(50), primary_key=True, default=new_id)
    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True, default=new_id)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_code = Column(String(20), nullable=False)  # ADMIN KB KBY DB DBY KOB
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Bulletin(Base):
    __tablename__ = "bulletins"
    id = Column(String(50), primary_key=True, default=new_id)
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    status = Column(String(50), default="DRAFT")
    created_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Section(Base):
    __tablename__ = "sections"
    id = Column(String(50), primary_key=True, default=new_id)
    bulletin_id = Column(String(50), ForeignKey("bulletins.id"), nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    heading_group_code = Column(String(10), nullable=True)
    heading_sub_group_code = Column(String(10), nullable=True)
    status = Column(String(50), default="SECTION_PREP")
    no_content = Column(Boolean, default=False)
    content_html = Column(Text, nullable=True)
    structured_tables = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    assigned_db_id = Column(String(50), nullable=True)
    assigned_dby_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Entry(Base):
    __tablename__ = "entries"
    id = Column(String(50), primary_key=True, default=new_id)
    section_id = Column(String(50), ForeignKey("sections.id"), nullable=False)
    content_html = Column(Text, nullable=True)
    structured_tables = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    order = Column(Integer, default=1)
    heading_group_code = Column(String(10), nullable=True)
    heading_sub_group_code = Column(String(10), nullable=True)
    approval_status = Column(String(20), default="DRAFT")
    created_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    created_by_role = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Log(Base):
    __tablename__ = "logs"
    id = Column(String(50), primary_key=True, default=new_id)
    action = Column(String(50), nullable=False)
    user_id = Column(String(50), nullable=True)
    user_name = Column(String(100), nullable=True)
    user_role = Column(String(20), nullable=True)
    bulletin_id = Column(String(50), nullable=True)
    section_id = Column(String(50), nullable=True)
    entry_id = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value_summary = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Archive(Base):
    __tablename__ = "archives"
    id = Column(String(50), primary_key=True, default=new_id)
    bulletin_id = Column(String(50), ForeignKey("bulletins.id"), nullable=False)
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    clean_html = Column(Text, nullable=True)
    logged_html = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    approved_by_chair = Column(String(100), nullable=True)
    clean_pdf_hash = Column(String(64), nullable=True)
    logged_view_hash = Column(String(64), nullable=True)
