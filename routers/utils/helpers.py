from typing import List
from datetime import datetime, date, timedelta

from models.events import (
    Event
)
from models.utils.enums import RepeatPatternEnum

# Helper function to generate repeat event instances
def generate_repeat_instances(
    event: Event, 
    start_date: date, 
    end_date: date
) -> List[dict]:
    """Generate event instances for repeat events within a date range"""
    instances = []
    
    if not event.repeat_pattern:
        # Single event - check if it falls within the range
        event_date = event.start_time.date()
        if start_date <= event_date <= end_date:
            instances.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "repeat_pattern": event.repeat_pattern,
                "repeat_until": event.repeat_until,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "is_repeat_instance": False,
                "original_date": event.start_time.date()
            })
        return instances
    
    # Handle repeat events
    current_date = max(start_date, event.start_time.date())
    repeat_end_date = min(end_date, event.repeat_until) if event.repeat_until else end_date
    
    if event.repeat_pattern == RepeatPatternEnum.DAILY:
        while current_date <= repeat_end_date:
            start_datetime = datetime.combine(current_date, event.start_time.time())
            end_datetime = datetime.combine(current_date, event.end_time.time())
            
            instances.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_time": start_datetime,
                "end_time": end_datetime,
                "repeat_pattern": event.repeat_pattern,
                "repeat_until": event.repeat_until,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "is_repeat_instance": True,
                "original_date": event.start_time.date(),
                "instance_date": current_date
            })
            current_date += timedelta(days=1)
    
    elif event.repeat_pattern == RepeatPatternEnum.WEEKLY:
        # Get the repeat days for this event
        repeat_days = [rd.day_of_week for rd in event.repeat_days]
        
        if not repeat_days:
            # If no specific days, use the original day
            repeat_days = [event.start_time.weekday()]
        
        while current_date <= repeat_end_date:
            # Convert Python weekday (0=Monday) to our format (0=Sunday)
            current_weekday = (current_date.weekday() + 1) % 7
            
            if current_weekday in repeat_days:
                start_datetime = datetime.combine(current_date, event.start_time.time())
                end_datetime = datetime.combine(current_date, event.end_time.time())
                
                instances.append({
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "event_type": event.event_type,
                    "start_time": start_datetime,
                    "end_time": end_datetime,
                    "repeat_pattern": event.repeat_pattern,
                    "repeat_until": event.repeat_until,
                    "created_at": event.created_at,
                    "updated_at": event.updated_at,
                    "is_repeat_instance": True,
                    "original_date": event.start_time.date(),
                    "instance_date": current_date
                })
            
            current_date += timedelta(days=1)
    
    elif event.repeat_pattern == RepeatPatternEnum.MONTHLY:
        original_day = event.start_time.day
        current_month_date = current_date.replace(day=1)
        
        while current_month_date <= repeat_end_date:
            try:
                # Try to create the date with the original day
                instance_date = current_month_date.replace(day=original_day)
                if start_date <= instance_date <= repeat_end_date:
                    start_datetime = datetime.combine(instance_date, event.start_time.time())
                    end_datetime = datetime.combine(instance_date, event.end_time.time())
                    
                    instances.append({
                        "id": event.id,
                        "title": event.title,
                        "description": event.description,
                        "event_type": event.event_type,
                        "start_time": start_datetime,
                        "end_time": end_datetime,
                        "repeat_pattern": event.repeat_pattern,
                        "repeat_until": event.repeat_until,
                        "created_at": event.created_at,
                        "updated_at": event.updated_at,
                        "is_repeat_instance": True,
                        "original_date": event.start_time.date(),
                        "instance_date": instance_date
                    })
            except ValueError:
                # Handle cases like Feb 30th - skip this month
                pass
            
            # Move to next month
            if current_month_date.month == 12:
                current_month_date = current_month_date.replace(year=current_month_date.year + 1, month=1)
            else:
                current_month_date = current_month_date.replace(month=current_month_date.month + 1)
    
    return instances
