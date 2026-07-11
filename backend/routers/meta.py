import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from core.taxonomy import get_taxonomy
from models import ProductTaxonomy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta", tags=["meta"])


class ProductCreate(BaseModel):
    product: str = Field(..., min_length=1, description="Product name is required")
    platform: str = Field(..., min_length=1, description="Platform is required (comma-separated)")
    sub_product: str = Field("", description="Sub product (optional, comma-separated)")
    solution: str = Field("", description="Solution (optional, comma-separated)")


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


@router.post("/products")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new product taxonomy entry.
    
    Checks for existing products (case-insensitive and whitespace-insensitive).
    If product exists, returns the existing product info.
    If product doesn't exist, creates a new taxonomy entry.
    """
    # Trim and normalize input
    product_name = data.product.strip()
    platform = data.platform.strip()
    sub_product = data.sub_product.strip() if data.sub_product else ""
    solution = data.solution.strip() if data.solution else ""
    
    if not product_name:
        raise HTTPException(status_code=400, detail="Product name is required")
    if not platform:
        raise HTTPException(status_code=400, detail="Platform is required")
    
    # Case-insensitive check for existing product
    existing_product = db.query(ProductTaxonomy).filter(
        func.lower(func.trim(ProductTaxonomy.product)) == func.lower(product_name)
    ).first()
    
    if existing_product:
        logger.info(f"Product already exists: {product_name}")
        # Return existing product info
        return {
            "product": existing_product.product,
            "platform": existing_product.platform,
            "sub_product": existing_product.sub_product,
            "solution": existing_product.solution,
            "existed": True
        }
    
    # Create new taxonomy entry
    new_taxonomy = ProductTaxonomy(
        product=product_name,
        platform=platform,
        sub_product=sub_product,
        solution=solution
    )
    db.add(new_taxonomy)
    db.commit()
    db.refresh(new_taxonomy)
    
    logger.info(f"Created new product taxonomy: {product_name}")
    
    return {
        "product": new_taxonomy.product,
        "platform": new_taxonomy.platform,
        "sub_product": new_taxonomy.sub_product,
        "solution": new_taxonomy.solution,
        "existed": False
    }
