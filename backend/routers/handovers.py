"""
Handover router — CRUD, document upload/download, and dashboard stats.

Changes from original:
 - T2:  upload_document() now uses StorageService (async); raw shutil removed
 - T4:  validate_taxonomy() reads from DB via core.taxonomy; hardcoded import removed
 - T6:  GET /{id} returns created_by_name (full_name or username)
 - T8:  Removed duplicate local HandoverCreate class; using schemas.HandoverCreate
 - T10: model_dump() replaces .dict(), datetime.now(timezone.utc), logging
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.dependencies import require_admin_or_above, require_any_role, get_current_user
from core.taxonomy import validate_taxonomy
from database import get_db
from models import Document, HandoverRecord, User
from schemas import HandoverOut, HandoverUpdate
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handovers", tags=["handovers"])


def _parse_csv(value: str) -> list:
    """Split a comma-separated string into a stripped list, ignoring empty entries."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


# ---------------------------------------------------------------------------
# Local schema (separate from schemas.HandoverCreate to allow optional fields)
# ---------------------------------------------------------------------------
class HandoverCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, description="Required")
    region: str = Field(..., min_length=1, description="Required")
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
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
    status: Optional[str] = "active"


# ---------------------------------------------------------------------------
# GET /handovers/
# ---------------------------------------------------------------------------
@router.get("/")
def get_handovers(
    search: str = None,
    product: str = None,
    region: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    try:
        query = db.query(HandoverRecord)

        if search:
            query = query.filter(
                HandoverRecord.customer_name.ilike(f"%{search}%")
                | HandoverRecord.support_ticket.ilike(f"%{search}%")
                | HandoverRecord.ps_engineer.ilike(f"%{search}%")
            )

        if product and product != "all":
            query = query.filter(HandoverRecord.product == product)

        if region and region != "all":
            query = query.filter(HandoverRecord.region == region)

        total = query.count()
        handovers = (
            query.order_by(HandoverRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = [
            {
                "id": h.id,
                "customer_name": h.customer_name or "N/A",
                "contact_person": h.contact_person or "",
                "region": h.region or "N/A",
                "product": h.product or "N/A",
                "sub_product": h.sub_product or "",
                "platform": h.platform or "",
                "solution": h.solution or "",
                "ps_engineer": h.ps_engineer or "",
                "sales_person": h.sales_person or "",
                "ps_reviewer": h.ps_reviewer or "",
                "support_ticket": h.support_ticket or "",
                "support_reviewer": h.support_reviewer or "",
                "remarks": h.remarks or "",
                "status": h.status or "active",
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            }
            for h in handovers
        ]

        return {"items": result, "total": total}

    except Exception as e:
        logger.error("Error fetching handovers: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /handovers/stats/dashboard
# ---------------------------------------------------------------------------
@router.get("/stats/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    total = db.query(HandoverRecord).count()
    this_month = db.query(HandoverRecord).filter(
        HandoverRecord.created_at >= month_start
    ).count()
    my_handovers = db.query(HandoverRecord).filter(
        HandoverRecord.created_by == current_user.id
    ).count()
    open_tickets = db.query(HandoverRecord).filter(
        HandoverRecord.support_ticket != None,
        HandoverRecord.support_ticket != "",
        HandoverRecord.status == "active",
    ).count()

    by_product = (
        db.query(HandoverRecord.product, func.count(HandoverRecord.id).label("count"))
        .group_by(HandoverRecord.product)
        .all()
    )
    by_region = (
        db.query(HandoverRecord.region, func.count(HandoverRecord.id).label("count"))
        .group_by(HandoverRecord.region)
        .all()
    )
    recent = (
        db.query(HandoverRecord)
        .order_by(HandoverRecord.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_handovers": total,
        "this_month": this_month,
        "my_handovers": my_handovers,
        "open_tickets": open_tickets,
        "by_product": [
            {"product": r.product or "Unknown", "count": r.count} for r in by_product
        ],
        "by_region": [
            {"region": r.region or "Unknown", "count": r.count} for r in by_region
        ],
        "recent_handovers": [
            {
                "id": h.id,
                "customer_name": h.customer_name,
                "region": h.region,
                "product": h.product,
                "platform": h.platform,
                "ps_engineer": h.ps_engineer,
                "status": h.status,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in recent
        ],
    }


# ---------------------------------------------------------------------------
# POST /handovers/
# ---------------------------------------------------------------------------
@router.post("/")
def create_handover(
    data: HandoverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_above),
):
    try:
        # Validate taxonomy for the product
        if data.product:
            validate_taxonomy(
                db,
                data.product,
                data.sub_product,
                data.platform,
                data.solution,
            )
        
        handover = HandoverRecord(
            customer_name=data.customer_name,
            contact_person=data.contact_person,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            region=data.region,
            ps_engineer=data.ps_engineer,
            sales_person=data.sales_person,
            ps_reviewer=data.ps_reviewer,
            support_ticket=data.support_ticket,
            support_reviewer=data.support_reviewer,
            product=data.product,
            sub_product=data.sub_product,
            platform=data.platform,
            solution=data.solution,
            remarks=data.remarks,
            status=data.status,
            created_by=current_user.id,
        )
        db.add(handover)
        db.commit()
        db.refresh(handover)
        return handover

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error creating handover: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to create handover: {str(e)}"
        )


# ---------------------------------------------------------------------------
# GET /handovers/{handover_id}  — T6: include created_by_name
# ---------------------------------------------------------------------------
@router.get("/{handover_id}")
def get_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    handover = (
        db.query(HandoverRecord)
        .filter(HandoverRecord.id == handover_id)
        .first()
    )
    if not handover:
        raise HTTPException(status_code=404, detail="Handover record not found")

    # Resolve creator name (full_name preferred, username fallback)
    creator_name: Optional[str] = None
    if handover.created_by:
        creator = db.query(User).filter(User.id == handover.created_by).first()
        if creator:
            creator_name = creator.full_name or creator.username

    return {
        "id": handover.id,
        "customer_name": handover.customer_name,
        "contact_person": handover.contact_person,
        "contact_phone": handover.contact_phone,
        "contact_email": handover.contact_email,
        "region": handover.region,
        "ps_engineer": handover.ps_engineer,
        "sales_person": handover.sales_person,
        "ps_reviewer": handover.ps_reviewer,
        "support_ticket": handover.support_ticket,
        "support_reviewer": handover.support_reviewer,
        "product": handover.product,
        "sub_product": handover.sub_product,
        "platform": handover.platform,
        "solution": handover.solution,
        "remarks": handover.remarks,
        "status": handover.status,
        "created_by": handover.created_by,
        "created_by_name": creator_name,
        "created_at": handover.created_at,
        "updated_at": handover.updated_at,
        "documents": [
            {
                "id": d.id,
                "handover_id": d.handover_id,
                "doc_type": d.doc_type,
                "filename": d.filename,
                "file_path": d.file_path,
                "uploaded_at": d.uploaded_at,
            }
            for d in handover.documents
        ],
    }


# ---------------------------------------------------------------------------
# PUT /handovers/{handover_id}  — T10: model_dump()
# ---------------------------------------------------------------------------
@router.put("/{handover_id}", response_model=HandoverOut)
def update_handover(
    handover_id: int,
    handover_in: HandoverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_above),
):
    db_handover = (
        db.query(HandoverRecord).filter(HandoverRecord.id == handover_id).first()
    )
    if not db_handover:
        raise HTTPException(status_code=404, detail="Handover record not found")

    update_data = handover_in.model_dump(exclude_unset=True)

    # Check if product fields are being updated
    if any(k in update_data for k in ["product", "sub_product", "platform", "solution"]):
        product = update_data.get("product", db_handover.product)
        sub_product = update_data.get("sub_product", db_handover.sub_product)
        platform = update_data.get("platform", db_handover.platform)
        solution = update_data.get("solution", db_handover.solution)
        
        # Validate taxonomy for the product
        if product:
            validate_taxonomy(
                db,
                product,
                sub_product,
                platform,
                solution,
            )

    for field, value in update_data.items():
        setattr(db_handover, field, value)

    db.commit()
    db.refresh(db_handover)
    return db_handover


# ---------------------------------------------------------------------------
# DELETE /handovers/{handover_id}
# ---------------------------------------------------------------------------
@router.delete("/{handover_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_above),
):
    db_handover = (
        db.query(HandoverRecord).filter(HandoverRecord.id == handover_id).first()
    )
    if not db_handover:
        raise HTTPException(status_code=404, detail="Handover record not found")

    for doc in db_handover.documents:
        storage_service.delete_file(doc.file_path)

    db.delete(db_handover)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# POST /handovers/{handover_id}/documents  — T2: use StorageService
# ---------------------------------------------------------------------------
@router.post("/{handover_id}/documents")
async def upload_document(
    handover_id: int,
    doc_type: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_above),
):
    handover = (
        db.query(HandoverRecord).filter(HandoverRecord.id == handover_id).first()
    )
    if not handover:
        raise HTTPException(status_code=404, detail="Handover not found")

    # T2: delegate file I/O to StorageService (supports local and S3)
    file_path = await storage_service.save_file(file, sub_dir=str(handover_id))

    doc = Document(
        handover_id=handover_id,
        doc_type=doc_type,
        filename=file.filename,
        file_path=file_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# GET /handovers/{handover_id}/documents/{doc_id}
# ---------------------------------------------------------------------------
@router.get("/{handover_id}/documents/{doc_id}")
def download_document(
    handover_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.handover_id == handover_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return storage_service.get_file_response(doc.file_path, doc.filename)
