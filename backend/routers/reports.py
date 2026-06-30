import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import HandoverRecord
from core.dependencies import require_any_role
from services.export_service import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_date_range(period: str) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "7d":
        return now - timedelta(days=7)
    elif period == "30d":
        return now - timedelta(days=30)
    elif period == "qtd":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        return datetime(now.year, quarter_start_month, 1, tzinfo=timezone.utc)
    elif period == "ytd":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc)
    else:
        return now - timedelta(days=30)


def get_handovers_for_period(db: Session, period: str):
    start_date = get_date_range(period)
    return (
        db.query(HandoverRecord)
        .filter(HandoverRecord.created_at >= start_date)
        .order_by(HandoverRecord.created_at.desc())
        .all()
    )


@router.get("/export")
def export_report(
    period: str = Query(default="30d"),
    format: str = Query(default="csv"),
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    try:
        handovers = get_handovers_for_period(db, period)
        date_str = datetime.now().strftime("%Y%m%d")
        filename_base = f"handover_report_{period}_{date_str}"

        if format == "csv":
            buffer = export_service.to_csv(handovers)
            return StreamingResponse(
                buffer,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.csv"
                },
            )

        elif format == "xlsx":
            buffer = export_service.to_xlsx(handovers)
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.xlsx"
                },
            )

        elif format == "pdf":
            buffer = export_service.to_pdf(handovers)
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                },
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use csv, xlsx, or pdf.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Export error for period=%s format=%s: %s", period, format, str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/summary")
def get_summary(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    try:
        handovers = get_handovers_for_period(db, period)
        return {"total": len(handovers), "period": period}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
