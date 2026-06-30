import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from core.taxonomy import get_taxonomy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/taxonomy")
def get_taxonomy_endpoint(db: Session = Depends(get_db)):
    """Return the full product taxonomy nested dict from the database."""
    return get_taxonomy(db)


@router.get("/taxonomy/{product}/{platform}")
def get_platform_taxonomy(
    product: str,
    platform: str,
    db: Session = Depends(get_db),
):
    taxonomy = get_taxonomy(db)

    if product not in taxonomy:
        raise HTTPException(status_code=404, detail=f"Product {product} not found")

    platforms = taxonomy[product].get("platforms", {})
    if platform not in platforms:
        raise HTTPException(
            status_code=404,
            detail=f"Platform {platform} not found for product {product}",
        )

    details = platforms[platform]
    return {
        "sub_products": details["sub_products"] if details["sub_products"] else None,
        "solutions": details["solutions"] if details["solutions"] else None,
    }
