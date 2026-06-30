from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class DocType(str, enum.Enum):
    HO_REPORT = "HO Report"
    PROJECT_SIGNOFF = "Project Signoff"
    SHOW_TECH = "Show Tech"
    OTHER = "Other"

class ProductEnum(str, enum.Enum):
    AVX = "AVX"
    APV = "APV"
    vAPV = "vAPV"
    AG = "AG"
    vxAG = "vxAG"
    ASF = "ASF"

class ProductTaxonomy(Base):
    __tablename__ = "product_taxonomy"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String, index=True, nullable=False)
    platform = Column(Text)  # Store as comma-separated or JSON string
    sub_product = Column(Text)
    solution = Column(Text)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    handovers = relationship("HandoverRecord", primaryjoin="User.id==HandoverRecord.created_by")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    region = Column(String)

class HandoverRecord(Base): 
    __tablename__ = "handover_records" 
 
    id = Column(Integer, primary_key=True, index=True) 
    
    # Customer info entered directly by user 
    customer_name = Column(String, nullable=True) 
    contact_person = Column(String, nullable=True) 
    contact_phone = Column(String, nullable=True) 
    contact_email = Column(String, nullable=True) 
    region = Column(String, nullable=True) 
    
    # Team info 
    ps_engineer = Column(String, nullable=True) 
    sales_person = Column(String, nullable=True) 
    ps_reviewer = Column(String, nullable=True) 
    support_ticket = Column(String, nullable=True) 
    support_reviewer = Column(String, nullable=True) 
    
    # Product info 
    product = Column(String, nullable=True) 
    sub_product = Column(String, nullable=True) 
    platform = Column(String, nullable=True) 
    solution = Column(String, nullable=True) 
    
    remarks = Column(String, nullable=True) 
    status = Column(String, default='active') 
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
 
    documents = relationship("Document", back_populates="handover") 

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    handover_id = Column(Integer, ForeignKey("handover_records.id"))
    doc_type = Column(Enum(DocType))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    handover = relationship("HandoverRecord", back_populates="documents")
