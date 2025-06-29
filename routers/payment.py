from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import date

from database import get_session
from models.payments import Payment, PaymentCreate, PaymentRead, PaymentUpdate

payment = APIRouter(prefix="/payment", tags=["payments"])

@payment.post("/", response_model=PaymentRead)
def create_payment(payment: PaymentCreate, session: Session = Depends(get_session)):
    """Create a new payment record."""
    db_payment = Payment.model_validate(payment)
    session.add(db_payment)
    session.commit()
    session.refresh(db_payment)
    return db_payment

@payment.get("/", response_model=List[PaymentRead])
def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    pupil_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=1900),
    session: Session = Depends(get_session)
):
    """Get all payments with optional filtering."""
    query = select(Payment)
    
    if pupil_id:
        query = query.where(Payment.pupil_id == pupil_id)
    if month:
        query = query.where(Payment.month == month)
    if year:
        query = query.where(Payment.year == year)
    
    query = query.offset(skip).limit(limit)
    payments = session.exec(query).all()
    return payments

@payment.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int, session: Session = Depends(get_session)):
    """Get a specific payment by ID."""
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@payment.put("/{payment_id}", response_model=PaymentRead)
def update_payment(
    payment_id: int, 
    payment_update: PaymentUpdate, 
    session: Session = Depends(get_session)
):
    """Update a payment record."""
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment_data = payment_update.model_dump(exclude_unset=True)
    for field, value in payment_data.items():
        setattr(payment, field, value)
    
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

@payment.delete("/{payment_id}")
def delete_payment(payment_id: int, session: Session = Depends(get_session)):
    """Delete a payment record."""
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    session.delete(payment)
    session.commit()
    return {"message": "Payment deleted successfully"}

@payment.get("/pupil/{pupil_id}", response_model=List[PaymentRead])
def get_payments_by_pupil(
    pupil_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session)
):
    """Get all payments for a specific pupil."""
    query = select(Payment).where(Payment.pupil_id == pupil_id).offset(skip).limit(limit)
    payments = session.exec(query).all()
    return payments

@payment.get("/pupil/{pupil_id}/month/{year}/{month}", response_model=List[PaymentRead])
def get_payments_by_pupil_and_month(
    pupil_id: int,
    year: int,
    month: int,
    session: Session = Depends(get_session)
):
    """Get payments for a specific pupil in a specific month/year."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if year < 1900:
        raise HTTPException(status_code=400, detail="Year must be 1900 or later")
    
    query = select(Payment).where(
        Payment.pupil_id == pupil_id,
        Payment.month == month,
        Payment.year == year
    )
    payments = session.exec(query).all()
    return payments
