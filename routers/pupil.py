from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from models.pupils import Pupil, PupilCreate, PupilRead, PupilUpdate
from database import get_session

pupil = APIRouter(prefix="/pupil", tags=["pupil"])

@pupil.post("/", response_model=PupilRead)
def create_pupil(pupil: PupilCreate, session: Session = Depends(get_session)):
    """Create a new pupil"""
    try:
        # Create new pupil instance
        db_pupil = Pupil.model_validate(pupil)
        
        # Add to session and commit
        session.add(db_pupil)
        session.commit()
        session.refresh(db_pupil)
        
        return db_pupil
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating pupil: {str(e)}")

@pupil.get("/", response_model=List[PupilRead])
def get_pupils(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by full name or email"),
    session: Session = Depends(get_session)
):
    """Get all pupils with optional pagination and search"""
    try:
        # Base query
        query = select(Pupil)
        
        # Add search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Pupil.full_name.ilike(search_term)) | 
                (Pupil.email.ilike(search_term))
            )
        
        # Add pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        pupils = session.exec(query).all()
        return pupils
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pupils: {str(e)}")

@pupil.get("/{pupil_id}", response_model=PupilRead)
def get_pupil(pupil_id: int, session: Session = Depends(get_session)):
    """Get a specific pupil by ID"""
    try:
        pupil = session.get(Pupil, pupil_id)
        if not pupil:
            raise HTTPException(status_code=404, detail="Pupil not found")
        return pupil
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pupil: {str(e)}")

@pupil.put("/{pupil_id}", response_model=PupilRead)
def update_pupil(
    pupil_id: int, 
    pupil_update: PupilUpdate, 
    session: Session = Depends(get_session)
):
    """Update a specific pupil"""
    try:
        # Get existing pupil
        db_pupil = session.get(Pupil, pupil_id)
        if not db_pupil:
            raise HTTPException(status_code=404, detail="Pupil not found")
        
        # Update fields that are provided (not None)
        pupil_data = pupil_update.model_dump(exclude_unset=True)
        for field, value in pupil_data.items():
            setattr(db_pupil, field, value)
        
        # Update the updated_at timestamp
        db_pupil.updated_at = datetime.now(datetime.timezone.utc)
        
        # Commit changes
        session.add(db_pupil)
        session.commit()
        session.refresh(db_pupil)
        
        return db_pupil
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating pupil: {str(e)}")

@pupil.patch("/{pupil_id}", response_model=PupilRead)
def patch_pupil(
    pupil_id: int, 
    pupil_update: PupilUpdate, 
    session: Session = Depends(get_session)
):
    """Partially update a specific pupil (same as PUT for this implementation)"""
    return update_pupil(pupil_id, pupil_update, session)

@pupil.delete("/{pupil_id}")
def delete_pupil(pupil_id: int, session: Session = Depends(get_session)):
    """Delete a specific pupil"""
    try:
        # Get existing pupil
        db_pupil = session.get(Pupil, pupil_id)
        if not db_pupil:
            raise HTTPException(status_code=404, detail="Pupil not found")
        
        # Delete the pupil
        session.delete(db_pupil)
        session.commit()
        
        return {"message": f"Pupil with ID {pupil_id} has been deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting pupil: {str(e)}")

@pupil.get("/search/by-name", response_model=List[PupilRead])
def search_pupils_by_name(
    name: str = Query(..., min_length=2, description="Name to search for"),
    session: Session = Depends(get_session)
):
    """Search pupils by full name"""
    try:
        query = select(Pupil).where(Pupil.full_name.ilike(f"%{name}%"))
        pupils = session.exec(query).all()
        return pupils
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching pupils: {str(e)}")

@pupil.get("/filter/by-gender/{gender}", response_model=List[PupilRead])
def get_pupils_by_gender(gender: str, session: Session = Depends(get_session)):
    """Get pupils filtered by gender"""
    try:
        query = select(Pupil).where(Pupil.gender == gender)
        pupils = session.exec(query).all()
        return pupils
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering pupils by gender: {str(e)}")

@pupil.get("/count/total")
def get_pupils_count(session: Session = Depends(get_session)):
    """Get total count of pupils"""
    try:
        query = select(Pupil)
        pupils = session.exec(query).all()
        return {"total_pupils": len(pupils)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting pupils: {str(e)}")
