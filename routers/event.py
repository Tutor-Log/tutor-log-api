from typing import List, Optional
from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, and_, or_
from sqlalchemy.orm import selectinload

from database import get_session
from models.events import (
    Event, EventCreate, EventRead, EventUpdate,
    EventRepeatDay, EventRepeatDayCreate, EventRepeatDayRead, EventRepeatDayUpdate, EventPupilUpdate
)
from models.event_pupil import EventPupil, EventPupilCreate, EventPupilRead
from models.utils.enums import RepeatPatternEnum, EventTypeEnum
from .utils.helpers import generate_repeat_instances
event = APIRouter(prefix="/events", tags=["events"])

@event.post("/", response_model=EventRead)
def create_event(
    event_data: EventCreate,
    repeat_days: Optional[List[int]] = None,
    owner_id: int = Query(..., description="ID of the event owner"),
    session: Session = Depends(get_session)
):
    """Create a new event with optional repeat days"""
    
    # Validate repeat days if provided
    if repeat_days:
        for day in repeat_days:
            if day < 0 or day > 6:
                raise HTTPException(
                    status_code=400, 
                    detail="Repeat days must be between 0 (Sunday) and 6 (Saturday)"
                )
    
    # Validate time logic
    if event_data.start_time >= event_data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time"
        )
    
    # Validate repeat pattern logic
    if event_data.repeat_pattern and event_data.repeat_pattern != RepeatPatternEnum.NONE:
        if event_data.repeat_pattern == RepeatPatternEnum.WEEKLY and not repeat_days:
            raise HTTPException(
                status_code=400,
                detail="Weekly repeat pattern requires repeat days"
            )
    
    # Create the event
    db_event = Event.model_validate(event_data)
    db_event.owner_id = owner_id
    db_event.created_at = datetime.now(timezone.utc)
    db_event.updated_at = datetime.now(timezone.utc)
    
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    
    # Add repeat days if provided
    if repeat_days and event_data.repeat_pattern == RepeatPatternEnum.WEEKLY:
        for day in repeat_days:
            repeat_day = EventRepeatDay(event_id=db_event.id, day_of_week=day)
            session.add(repeat_day)
        session.commit()
        session.refresh(db_event)
    
    return db_event

@event.get("/", response_model=List[dict])
def get_events(
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    event_type: Optional[EventTypeEnum] = Query(None, description="Filter by event type"),
    include_repeats: bool = Query(True, description="Include repeat event instances"),
    owner_id: Optional[int] = Query(None, description="Filter events by owner"),
    session: Session = Depends(get_session)
):
    """Get events with optional filtering and repeat instance generation"""
    
    # Build base query
    query = select(Event).options(selectinload(Event.repeat_days))
    
    # Apply event type filter
    if event_type:
        query = query.where(Event.event_type == event_type)
    
    # Apply owner filter
    if owner_id:
        query = query.where(Event.owner_id == owner_id)
    
    # If no date range specified, default to current month
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        # Last day of current month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    
    # Filter events that could potentially have instances in the date range
    query = query.where(
        or_(
            # Single events within range
            and_(
                Event.repeat_pattern.is_(None),
                Event.start_time >= datetime.combine(start_date, datetime.min.time()),
                Event.start_time <= datetime.combine(end_date, datetime.max.time())
            ),
            # Repeat events that start before or during the range and don't end before the range
            and_(
                Event.repeat_pattern.isnot(None),
                Event.start_time <= datetime.combine(end_date, datetime.max.time()),
                or_(
                    Event.repeat_until.is_(None),
                    Event.repeat_until >= start_date
                )
            )
        )
    )
    
    events = session.exec(query).all()
    
    if not include_repeats:
        return [event.model_dump() for event in events]
    
    # Generate repeat instances
    all_instances = []
    for event in events:
        instances = generate_repeat_instances(event, start_date, end_date)
        all_instances.extend(instances)
    
    # Sort by start time
    all_instances.sort(key=lambda x: x["start_time"])
    
    return all_instances

@event.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: Session = Depends(get_session)):
    """Get a specific event by ID"""
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@event.put("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    repeat_days: Optional[List[int]] = None,
    update_future_only: bool = Query(False, description="For repeat events, only update future instances"),
    current_user_id: int = Query(..., description="ID of the current user"),
    session: Session = Depends(get_session)
):
    """Update an event with careful handling of repeat events"""
    
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    
    # Validate repeat days if provided
    if repeat_days:
        for day in repeat_days:
            if day < 0 or day > 6:
                raise HTTPException(
                    status_code=400,
                    detail="Repeat days must be between 0 (Sunday) and 6 (Saturday)"
                )
    
    # Handle repeat event updates
    if event.repeat_pattern and update_future_only:
        # Create a new event for future instances
        new_event = Event(**event.model_dump())
        new_event.owner_id = current_user_id
        
        # Set the repeat_until date for the original event to yesterday
        today = date.today()
        event.repeat_until = today - timedelta(days=1)
        event.updated_at = datetime.now(timezone.utc)
        session.add(event)
        
        # Update the new event with the changes
        update_data = event_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(new_event, field, value)
        
        # Set the start date of the new event to today
        new_event.start_time = datetime.combine(today, new_event.start_time.time())
        if new_event.end_time:
            time_diff = new_event.end_time - event.start_time
            new_event.end_time = new_event.start_time + time_diff
        
        new_event.created_at = datetime.now(timezone.utc)
        new_event.updated_at = datetime.now(timezone.utc)
        session.add(new_event)
        
        # Copy repeat days to new event if it's weekly
        if new_event.repeat_pattern == RepeatPatternEnum.WEEKLY and repeat_days is not None:
            for day in repeat_days:
                repeat_day = EventRepeatDay(event_id=new_event.id, day_of_week=day)
                session.add(repeat_day)
        
        session.commit()
        session.refresh(new_event)
        return new_event
    
    # Update event fields for non-repeat or all instances
    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    # Validate time logic if times are being updated
    if event_update.start_time or event_update.end_time:
        if event.start_time >= event.end_time:
            raise HTTPException(
                status_code=400,
                detail="Start time must be before end time"
            )
    
    event.updated_at = datetime.now(timezone.utc)
    
    # Update repeat days if provided and it's a weekly repeat
    if repeat_days is not None and (
        event.repeat_pattern == RepeatPatternEnum.WEEKLY or 
        event_update.repeat_pattern == RepeatPatternEnum.WEEKLY
    ):
        # Remove existing repeat days
        existing_repeat_days = session.exec(
            select(EventRepeatDay).where(EventRepeatDay.event_id == event_id)
        ).all()
        for repeat_day in existing_repeat_days:
            session.delete(repeat_day)
        
        # Add new repeat days
        for day in repeat_days:
            repeat_day = EventRepeatDay(event_id=event_id, day_of_week=day)
            session.add(repeat_day)
    
    session.add(event)
    session.commit()
    session.refresh(event)
    
    return event

@event.delete("/{event_id}")
def delete_event(
    event_id: int,
    delete_future_only: bool = Query(False, description="For repeat events, only delete future instances"),
    current_user_id: int = Query(..., description="ID of the current user"),
    session: Session = Depends(get_session)
):
    """Delete an event with options for repeat events"""
    
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.owner_id != current_user_id.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")
    
    if event.repeat_pattern and delete_future_only:
        # For repeat events, we could set repeat_until to today
        # This effectively "deletes" future instances
        event.repeat_until = date.today()
        event.updated_at = datetime.now(timezone.utc)
        session.add(event)
        session.commit()
        return {"message": "Future instances of repeat event deleted"}
    else:
        # Delete the entire event and its repeat days
        repeat_days = session.exec(
            select(EventRepeatDay).where(EventRepeatDay.event_id == event_id)
        ).all()
        for repeat_day in repeat_days:
            session.delete(repeat_day)
        
        session.delete(event)
        session.commit()
        return {"message": "Event deleted successfully"}

@event.get("/{event_id}/repeat-days", response_model=List[EventRepeatDayRead])
def get_event_repeat_days(event_id: int, session: Session = Depends(get_session)):
    """Get repeat days for an event"""
    
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    repeat_days = session.exec(
        select(EventRepeatDay).where(EventRepeatDay.event_id == event_id)
    ).all()
    
    return repeat_days

@event.post("/{event_id}/repeat-days", response_model=List[EventRepeatDayRead], status_code=status.HTTP_201_CREATED)
def create_event_repeat_days(
    event_id: int,
    repeat_days: List[EventRepeatDayCreate],
    session: Session = Depends(get_session)
):
    """Create multiple repeat days for an event"""
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create repeat days with event_id
    db_repeat_days = []
    for repeat_day in repeat_days:
        repeat_day_data = repeat_day.dict()
        repeat_day_data["event_id"] = event_id
        db_repeat_day = EventRepeatDay(**repeat_day_data)
        db_repeat_days.append(db_repeat_day)
    
    session.add_all(db_repeat_days)
    session.commit()
    for repeat_day in db_repeat_days:
        session.refresh(repeat_day)
    return db_repeat_days

@event.put("/{event_id}/repeat-days", response_model=List[EventRepeatDayRead])
def update_event_repeat_days(
    event_id: int,
    repeat_days: List[EventRepeatDayUpdate],
    session: Session = Depends(get_session)
):
    """Update multiple repeat days for an event"""
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update repeat days
    db_repeat_days = []
    for repeat_day in repeat_days:
        repeat_day_data = repeat_day.dict(exclude_unset=True)
        db_repeat_day = session.get(EventRepeatDay, repeat_day.id)
        if not db_repeat_day or db_repeat_day.event_id != event_id:
            raise HTTPException(status_code=404, detail=f"Repeat day {repeat_day.id} not found for this event")
        
        for key, value in repeat_day_data.items():
            setattr(db_repeat_day, key, value)
        db_repeat_days.append(db_repeat_day)
    
    session.add_all(db_repeat_days)
    session.commit()
    for repeat_day in db_repeat_days:
        session.refresh(repeat_day)
    return db_repeat_days

@event.delete("/{event_id}/repeat-days", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_repeat_days(
    event_id: int,
    repeat_day_ids: List[int],
    session: Session = Depends(get_session)
):
    """Delete multiple repeat days from an event"""
    statement = select(EventRepeatDay).where(
        EventRepeatDay.event_id == event_id,
        EventRepeatDay.id.in_(repeat_day_ids)
    )
    repeat_days = session.exec(statement).all()
    
    if not repeat_days:
        raise HTTPException(status_code=404, detail="No matching repeat days found")
    
    for repeat_day in repeat_days:
        session.delete(repeat_day)
    session.commit()

@event.get("/{event_id}/pupils", response_model=List[EventPupilRead])
def get_event_pupils(
    event_id: int,
    session: Session = Depends(get_session)
):
    """Get all pupils assigned to an event"""
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    statement = select(EventPupil).where(EventPupil.event_id == event_id)
    event_pupils = session.exec(statement).all()
    return event_pupils

@event.post("/{event_id}/pupils", response_model=List[EventPupilRead], status_code=status.HTTP_201_CREATED)
def add_pupils_to_event(
    event_id: int,
    pupil_assignments: List[EventPupilCreate],
    session: Session = Depends(get_session)
):
    """Add multiple pupils to an event"""
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create pupil assignments with event_id
    db_event_pupils = []
    for pupil_assignment in pupil_assignments:
        pupil_data = pupil_assignment.dict()
        pupil_data["event_id"] = event_id
        db_event_pupil = EventPupil(**pupil_data)
        db_event_pupils.append(db_event_pupil)
    
    session.add_all(db_event_pupils)
    session.commit()
    for pupil in db_event_pupils:
        session.refresh(pupil)
    return db_event_pupils

@event.put("/{event_id}/pupils", response_model=List[EventPupilRead])
def update_event_pupils(
    event_id: int,
    pupil_assignments: List[EventPupilUpdate],
    session: Session = Depends(get_session)
):
    """Update multiple pupil assignments for an event"""
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_event_pupils = []
    for pupil_assignment in pupil_assignments:
        pupil_data = pupil_assignment.dict(exclude_unset=True)
        db_event_pupil = session.get(EventPupil, pupil_assignment.id)
        if not db_event_pupil or db_event_pupil.event_id != event_id:
            raise HTTPException(status_code=404, detail=f"Pupil assignment {pupil_assignment.id} not found for this event")
        
        for key, value in pupil_data.items():
            setattr(db_event_pupil, key, value)
        db_event_pupils.append(db_event_pupil)
    
    session.add_all(db_event_pupils)
    session.commit()
    for pupil in db_event_pupils:
        session.refresh(pupil)
    return db_event_pupils

@event.delete("/{event_id}/pupils", status_code=status.HTTP_204_NO_CONTENT)
def remove_pupils_from_event(
    event_id: int,
    pupil_ids: List[int],
    session: Session = Depends(get_session)
):
    """Remove multiple pupils from an event"""
    statement = select(EventPupil).where(
        EventPupil.event_id == event_id,
        EventPupil.pupil_id.in_(pupil_ids)
    )
    event_pupils = session.exec(statement).all()
    
    if not event_pupils:
        raise HTTPException(status_code=404, detail="No pupil assignments found")
    
    for event_pupil in event_pupils:
        session.delete(event_pupil)
    session.commit()
    
