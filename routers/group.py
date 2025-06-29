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

@group.post("/{group_id}/members", response_model=PupilGroupMembershipRead, status_code=status.HTTP_201_CREATED)
def add_pupil_to_group(
    group_id: int,
    membership: PupilGroupMembershipCreate,
    current_user_id: int,
    session: Session = Depends(get_session)
):
    """Add a pupil to a group"""
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
    
    # Check if membership already exists
    statement = select(PupilGroupMembership).where(
        PupilGroupMembership.pupil_id == membership.pupil_id,
        PupilGroupMembership.group_id == group_id
    )
    existing_membership = session.exec(statement).first()
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pupil is already a member of this group"
        )
    
    # Ensure the membership has the correct group_id
    membership_data = membership.model_dump()
    membership_data["group_id"] = group_id
    
    db_membership = PupilGroupMembership(**membership_data)
    session.add(db_membership)
    session.commit()
    session.refresh(db_membership)
    return db_membership

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
