from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship

from models.utils.enums import GenderEnum

# Pupil Model
class PupilBase(SQLModel):
    full_name: str = Field(max_length=255)
    email: Optional[str] = Field(default=None, max_length=320, unique=True)
    mobile: str = Field(max_length=15)
    father_name: str = Field(max_length=255)
    mother_name: str = Field(max_length=255)
    date_of_birth: date
    gender: GenderEnum
    enrolled_on: date
    owner_id: int = Field(foreign_key="users.id")

class Pupil(PupilBase, table=True):
    __tablename__ = "pupils"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    
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
