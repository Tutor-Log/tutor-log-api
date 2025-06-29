from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship

from models.utils.enums import RepeatPatternEnum, EventTypeEnum

# Event Model
class EventBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    event_type: EventTypeEnum
    start_time: datetime
    end_time: datetime
    repeat_pattern: Optional[RepeatPatternEnum] = None
    repeat_until: Optional[date] = None

class Event(EventBase, table=True):
    __tablename__ = "events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - using string forward references
    repeat_days: List["EventRepeatDay"] = Relationship(back_populates="event")
    event_pupils: List["EventPupil"] = Relationship(back_populates="event")

class EventCreate(EventBase):
    pass

class EventRead(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

class EventUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventTypeEnum] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    repeat_pattern: Optional[RepeatPatternEnum] = None
    repeat_until: Optional[date] = None

# Event Repeat Days Model
class EventRepeatDayBase(SQLModel):
    event_id: int = Field(foreign_key="events.id")
    day_of_week: int = Field(ge=0, le=6)  # 0=Sunday to 6=Saturday

class EventRepeatDay(EventRepeatDayBase, table=True):
    __tablename__ = "event_repeat_days"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships - using string forward reference
    event: Optional["Event"] = Relationship(back_populates="repeat_days")

class EventRepeatDayCreate(EventRepeatDayBase):
    pass

class EventRepeatDayRead(EventRepeatDayBase):
    id: int
