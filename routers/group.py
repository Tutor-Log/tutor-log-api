from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models.groups import (
    Group, 
    GroupCreate, 
    GroupRead, 
    GroupUpdate,
    PupilGroupMembership,
    PupilGroupMembershipCreate,
    PupilGroupMembershipRead
)

group = APIRouter(prefix="/group", tags=["groups"])

# Group CRUD Operations

@group.post("/", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, current_user_id: int, session: Session = Depends(get_session)):
    """Create a new group"""
    db_group = Group.model_validate(group)
    db_group.owner_id = current_user_id
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group

@group.get("/", response_model=List[GroupRead])
def get_groups(current_user_id: int, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Get all groups with pagination"""
    statement = select(Group).where(Group.owner_id == current_user_id).offset(skip).limit(limit)
    groups = session.exec(statement).all()
    return groups

@group.get("/search", response_model=List[GroupRead])
def search_group_by_name(current_user_id: int, name: str = None, session: Session = Depends(get_session)):
    """Search for groups by name"""
    statement = select(Group).where(Group.name.contains(name), Group.owner_id == current_user_id)
    groups = session.exec(statement).all()
    return groups

@group.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, current_user_id: int, session: Session = Depends(get_session)):
    """Get a specific group by ID"""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group"
        )
    return group

@group.put("/{group_id}", response_model=GroupRead)
def update_group(
    group_id: int, 
    group_update: GroupUpdate,
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Update a group"""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this group"
        )
    
    group_data = group_update.model_dump(exclude_unset=True)
    for field, value in group_data.items():
        setattr(group, field, value)
    
    session.add(group)
    session.commit()
    session.refresh(group)
    return group

@group.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, current_user_id: int, session: Session = Depends(get_session)):
    """Delete a group"""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group"
        )
    
    session.delete(group)
    session.commit()

# Pupil Group Membership Operations

@group.post("/{group_id}/members", response_model=List[PupilGroupMembershipRead], status_code=status.HTTP_201_CREATED)
def add_pupils_to_group(
    group_id: int,
    memberships: List[PupilGroupMembershipCreate],
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Add multiple pupils to a group"""
    # Verify group exists and user owns it
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this group"
        )
    
    # Check if any memberships already exist
    pupil_ids = [membership.pupil_id for membership in memberships]
    statement = select(PupilGroupMembership).where(
        PupilGroupMembership.pupil_id.in_(pupil_ids),
        PupilGroupMembership.group_id == group_id
    )
    existing_memberships = session.exec(statement).all()
    if existing_memberships:
        existing_pupil_ids = [m.pupil_id for m in existing_memberships]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pupils with IDs {existing_pupil_ids} are already members of this group"
        )
    
    # Create new memberships
    db_memberships = []
    for membership in memberships:
        membership_data = membership.model_dump()
        membership_data["group_id"] = group_id
        db_membership = PupilGroupMembership(**membership_data)
        db_memberships.append(db_membership)
    
    session.add_all(db_memberships)
    session.commit()
    for membership in db_memberships:
        session.refresh(membership)
    return db_memberships

@group.put("/{group_id}/members", response_model=List[PupilGroupMembershipRead])
def update_group_members(
    group_id: int,
    memberships: List[PupilGroupMembershipCreate],
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Update group members - add new ones and remove those not in the request"""
    # Verify group exists and user owns it
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this group"
        )
    
    # Get requested pupil IDs
    requested_pupil_ids = [membership.pupil_id for membership in memberships]
    
    # Get current memberships
    statement = select(PupilGroupMembership).where(PupilGroupMembership.group_id == group_id)
    current_memberships = session.exec(statement).all()
    
    # Remove memberships not in the request
    for membership in current_memberships:
        if membership.pupil_id not in requested_pupil_ids:
            session.delete(membership)
    
    # Add new memberships
    db_memberships = []
    current_pupil_ids = [m.pupil_id for m in current_memberships]
    for membership in memberships:
        if membership.pupil_id not in current_pupil_ids:
            membership_data = membership.model_dump()
            membership_data["group_id"] = group_id
            db_membership = PupilGroupMembership(**membership_data)
            db_memberships.append(db_membership)
    
    session.add_all(db_memberships)
    session.commit()
    
    # Get all updated memberships
    statement = select(PupilGroupMembership).where(PupilGroupMembership.group_id == group_id)
    updated_memberships = session.exec(statement).all()
    return updated_memberships

@group.get("/{group_id}/members", response_model=List[PupilGroupMembershipRead])
def get_group_members(group_id: int, current_user_id: int, session: Session = Depends(get_session)):
    """Get all members of a group"""
    # Verify group exists and user owns it
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group"
        )
    
    statement = select(PupilGroupMembership).where(PupilGroupMembership.group_id == group_id)
    memberships = session.exec(statement).all()
    return memberships

@group.delete("/{group_id}/members/{pupil_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pupil_from_group(
    group_id: int,
    pupil_id: int,
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Remove a pupil from a group"""
    # Verify group exists and user owns it
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this group"
        )

    statement = select(PupilGroupMembership).where(
        PupilGroupMembership.pupil_id == pupil_id,
        PupilGroupMembership.group_id == group_id
    )
    membership = session.exec(statement).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    session.delete(membership)
    session.commit()

@group.get("/{group_id}/members/{pupil_id}", response_model=PupilGroupMembershipRead)
def get_group_membership(
    group_id: int,
    pupil_id: int,
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Get specific membership details"""
    # Verify group exists and user owns it
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    if group.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group"
        )

    statement = select(PupilGroupMembership).where(
        PupilGroupMembership.pupil_id == pupil_id,
        PupilGroupMembership.group_id == group_id
    )
    membership = session.exec(statement).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    return membership
