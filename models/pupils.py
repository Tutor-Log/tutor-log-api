from typing import Optional, List
from datetime import datetime, timezone, date
from sqlmodel import SQLModel, Field, Relationship

from models.utils.enums import GenderEnum

# Pupil Model
class PupilBase(SQLModel):
    full_name: str = Field(max_length=255)
    email: str = Field(max_length=320, unique=True)
    mobile: str = Field(max_length=15)
    father_name: Optional[str] = Field(default=None, max_length=255)
    mother_name: Optional[str] = Field(default=None, max_length=255)
    date_of_birth: Optional[date] = Field(default=None)
    gender: Optional[GenderEnum] = Field(default=None)
    enrolled_on: date
    owner_id: int = Field(foreign_key="users.id")

class Pupil(PupilBase, table=True):
    __tablename__ = "pupils"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships - using string forward references
    user: "User" = Relationship(back_populates="pupils")
    group_memberships: List["PupilGroupMembership"] = Relationship(back_populates="pupil")
    event_pupils: List["EventPupil"] = Relationship(back_populates="pupil")
    payments: List["Payment"] = Relationship(back_populates="pupil")

class PupilCreate(PupilBase):
    pass

class PupilRead(PupilBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PupilUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    enrolled_on: Optional[date] = None
