from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# Users Model
class UserBase(SQLModel):
    google_user_id: str = Field(max_length=255, unique=True, index=True)
    email: str = Field(max_length=320, unique=True, index=True)
    full_name: str = Field(max_length=255)
    profile_pic_url: Optional[str] = None
    last_login_at: Optional[datetime] = None

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    events: List["Event"] = Relationship(back_populates="owner")
    pupils: List["Pupil"] = Relationship(back_populates="user")
    groups: List["Group"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    created_at: datetime

class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
