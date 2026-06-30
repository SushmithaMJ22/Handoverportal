"""
Taxonomy helpers.

The canonical source of truth is the `product_taxonomy` database table
(seeded via seed_taxonomy.py). The hardcoded TAXONOMY dict below serves as
a last-resort fallback during initial setup before the DB is seeded.

Use `get_taxonomy(db)` everywhere instead of referencing TAXONOMY directly.
"""
import json
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback constant (used only when DB table is empty / not yet seeded)
# ---------------------------------------------------------------------------
TAXONOMY: Dict[str, Any] = {
    "AVX": {
        "platforms": {
            "AVX 9900": {"sub_products": ["vAPV"], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "AVX 7900": {"sub_products": ["vxAG"], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AVX 9900 (vASF)": {"sub_products": ["vASF"], "solutions": ["WAF", "DDOS"]},
            "AVX 5800": {"sub_products": [], "solutions": []},
            "AVX 7800": {"sub_products": ["vAMP", "ZTAG"], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AVX 9800": {"sub_products": ["Struxture Inmotion"], "solutions": []},
            "AVX 9800 6VS": {"sub_products": ["Struxture Endpoint"], "solutions": []},
            "AVX 7600": {"sub_products": [], "solutions": []},
            "AVX 10650": {"sub_products": [], "solutions": []},
        }
    },
    "APV": {
        "platforms": {
            "APV 1900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 2900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 5900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 7900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 9900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 10900": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 1800": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 2800": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 5800": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 7800": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "APV 9800": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
        }
    },
    "vAPV": {
        "platforms": {
            "VMware": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "Nutanix": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
            "RHVP": {"sub_products": [], "solutions": ["SLB", "LLB", "GSLB", "SSLI", "SSLO"]},
        }
    },
    "AG": {
        "platforms": {
            "AG 1000 vS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AG 1100 vS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AG 1200 vS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AG 1500 vS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AG 1500 FIPS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "AG 1600 vS": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
        }
    },
    "vxAG": {
        "platforms": {
            "VMware": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "Nutanix": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
            "RHVP": {"sub_products": [], "solutions": ["L3 VPN", "L4 VPN", "SSL VPN", "DD"]},
        }
    },
    "ASF": {
        "platforms": {
            "ASF 1800": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
            "ASF 2800": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
            "ASF 5800": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
            "VMware": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
            "Nutanix": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
            "RHVP": {"sub_products": [], "solutions": ["WAF", "DDOS"]},
        }
    },
}


def _parse_csv(value: str) -> list:
    """Split a comma-separated string into a stripped list, ignoring empty entries."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def get_taxonomy(db: Session) -> Dict[str, Any]:
    """
    Build the nested taxonomy dict from the ProductTaxonomy DB table.

    The DB stores each product as a flat row with comma-separated platform/
    sub_product/solution strings. This function expands them into the nested
    structure the frontend cascading dropdowns expect:

        {
          "AVX": {
            "platforms": {
              "AVX 9900": {"sub_products": [...], "solutions": [...]},
              ...
            }
          },
          ...
        }

    Falls back to the hardcoded TAXONOMY constant if the DB table is empty
    (e.g., before the first seed run).
    """
    from models import ProductTaxonomy  # local import to avoid circular deps

    try:
        rows = db.query(ProductTaxonomy).all()
    except Exception as e:
        logger.warning("Failed to query ProductTaxonomy table, using fallback: %s", e)
        return TAXONOMY

    if not rows:
        logger.warning(
            "ProductTaxonomy table is empty — using hardcoded fallback. "
            "Run seed_taxonomy.py to populate the database."
        )
        return TAXONOMY

    result: Dict[str, Any] = {}
    for row in rows:
        platforms_list = _parse_csv(row.platform)
        sub_products_list = _parse_csv(row.sub_product)
        solutions_list = _parse_csv(row.solution)

        platforms_dict: Dict[str, Any] = {}
        for platform in platforms_list:
            platforms_dict[platform] = {
                "sub_products": sub_products_list,
                "solutions": solutions_list,
            }

        result[row.product] = {"platforms": platforms_dict}

    return result


def validate_taxonomy(db: Session, product: str, sub_product: str, platform: str, solution: str) -> None:
    """
    Validate that product/platform/sub_product/solution values are consistent
    with what is stored in the ProductTaxonomy table.
    Raises HTTPException on validation failure.
    """
    from fastapi import HTTPException

    taxonomy = get_taxonomy(db)

    if product not in taxonomy:
        raise HTTPException(status_code=400, detail=f"Invalid product: {product}")

    platforms = taxonomy[product].get("platforms", {})
    if platform not in platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}' for product '{product}'",
        )

    details = platforms[platform]
    valid_sub_products = details.get("sub_products", [])
    valid_solutions = details.get("solutions", [])

    if sub_product and valid_sub_products and sub_product not in valid_sub_products:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sub-product '{sub_product}' for platform '{platform}'",
        )

    if sub_product and not valid_sub_products:
        raise HTTPException(
            status_code=400,
            detail=f"Sub-product must be null for platform '{platform}'",
        )

    if solution and valid_solutions and solution not in valid_solutions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid solution '{solution}' for platform '{platform}'",
        )

    if solution and not valid_solutions:
        raise HTTPException(
            status_code=400,
            detail=f"Solution must be null for platform '{platform}'",
        )
