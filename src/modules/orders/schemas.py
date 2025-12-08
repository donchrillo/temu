"""Order Schemas - API Input/Output Validation"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class OrderCreate(BaseModel):
    """Input Schema: Neue Order erstellen"""
    bestell_id: str = Field(..., min_length=1)
    vorname_empfaenger: str
    nachname_empfaenger: str
    email: EmailStr
    
    class Config:
        example = {
            "bestell_id": "PO-076-07254990055033717",
            "vorname_empfaenger": "Max",
            "nachname_empfaenger": "Mustermann",
            "email": "max@example.com"
        }

class OrderResponse(BaseModel):
    """Output Schema: Order API Response"""
    id: int
    bestell_id: str
    vorname_empfaenger: str
    nachname_empfaenger: str
    email: str
    status: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # SQLAlchemy Kompatibilität

class OrderListResponse(BaseModel):
    """Output Schema: Mehrere Orders"""
    total: int
    items: list[OrderResponse]
