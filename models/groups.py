from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

from models.pupils import Pupil

# Group Model
class GroupBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    owner_id: int = Field(foreign_key="users.id")

class Group(GroupBase, table=True):
    __tablename__ = "groups"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="groups")
    pupil_memberships: List["PupilGroupMembership"] = Relationship(back_populates="group")

class GroupCreate(GroupBase):
    pass

class GroupRead(GroupBase):
    id: int
    created_at: datetime

class GroupUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Pupil Group Membership (Junction Table)
class PupilGroupMembershipBase(SQLModel):
    pupil_id: int = Field(foreign_key="pupils.id")
    group_id: int = Field(foreign_key="groups.id")

class PupilGroupMembership(PupilGroupMembershipBase, table=True):
    __tablename__ = "pupil_group_membership"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    pupil: Optional[Pupil] = Relationship(back_populates="group_memberships")
    group: Optional[Group] = Relationship(back_populates="pupil_memberships")

class PupilGroupMembershipCreate(PupilGroupMembershipBase):
    pass

class PupilGroupMembershipRead(PupilGroupMembershipBase):
    id: int
    joined_at: datetime
