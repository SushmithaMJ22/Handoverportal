from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
from models import UserRole, DocType
import re

# User Schemas
class UserBase(BaseModel):
    full_name: Optional[str] = None
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER

def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*]', password):
        raise ValueError("Password must contain at least one special character (!@#$%^&*)")
    return password

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, password: Optional[str]) -> Optional[str]:
        if password is not None:
            return validate_password_strength(password)
        return password

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: UserOut

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    region: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int

    class Config:
        from_attributes = True

# Document Schemas
class DocumentBase(BaseModel):
    doc_type: DocType
    filename: str

class DocumentOut(DocumentBase):
    id: int
    handover_id: int
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Handover Schemas
class HandoverBase(BaseModel):
    customer_name: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    region: str
    ps_engineer: Optional[str] = None
    sales_person: Optional[str] = None
    ps_reviewer: Optional[str] = None
    support_ticket: Optional[str] = None
    support_reviewer: Optional[str] = None
    product: str
    sub_product: Optional[str] = None
    platform: str
    solution: Optional[str] = None
    remarks: Optional[str] = None
    status: str = "Pending"

class HandoverCreate(HandoverBase):
    pass

class HandoverUpdate(BaseModel):
    customer_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    region: Optional[str] = None
    ps_engineer: Optional[str] = None
    sales_person: Optional[str] = None
    ps_reviewer: Optional[str] = None
    support_ticket: Optional[str] = None
    support_reviewer: Optional[str] = None
    product: Optional[str] = None
    sub_product: Optional[str] = None
    platform: Optional[str] = None
    solution: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[str] = None

# Taxonomy Schemas
class TaxonomyOut(BaseModel):
    product: str
    platforms: List[str]
    sub_products: List[str]
    solutions: List[str]

class HandoverOut(HandoverBase):
    id: int
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    documents: List[DocumentOut] = []

    class Config:
        from_attributes = True

# Report Schemas
class ReportSummary(BaseModel):
    total_handovers: int
    by_product: dict
    by_region: dict
    recent_activity: List[HandoverOut]
