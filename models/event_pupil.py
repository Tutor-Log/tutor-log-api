from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# Event Pupils (Junction Table)
class EventPupilBase(SQLModel):
    event_id: int = Field(foreign_key="events.id")
    pupil_id: int = Field(foreign_key="pupils.id")

class EventPupil(EventPupilBase, table=True):
    __tablename__ = "event_pupils"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - using string forward references
    event: Optional["Event"] = Relationship(back_populates="event_pupils")
    pupil: Optional["Pupil"] = Relationship(back_populates="event_pupils")

class EventPupilCreate(EventPupilBase):
    pass

class EventPupilRead(EventPupilBase):
    id: int
    added_at: datetime
