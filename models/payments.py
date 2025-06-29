from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship

from models.utils.enums import PaymentModeEnum
from models.pupils import Pupil

# Payment Model
class PaymentBase(SQLModel):
    pupil_id: int = Field(foreign_key="pupils.id")
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    month: int = Field(ge=1, le=12)  # 1-12 for January-December
    year: int = Field(ge=1900)
    payment_date: date
    payment_mode: PaymentModeEnum
    notes: Optional[str] = None

class Payment(PaymentBase, table=True):
    __tablename__ = "payments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    pupil: Optional[Pupil] = Relationship(back_populates="payments")

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: int
    created_at: datetime

class PaymentUpdate(SQLModel):
    amount: Optional[Decimal] = None
    month: Optional[int] = None
    year: Optional[int] = None
    payment_date: Optional[date] = None
    payment_mode: Optional[PaymentModeEnum] = None
    notes: Optional[str] = None
