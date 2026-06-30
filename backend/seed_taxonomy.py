from database import SessionLocal
from models import ProductTaxonomy

TAXONOMY_DATA = [
    {
        "product": "AVX",
        "platform": "AVX 9900,AVX 7900,AVX 5800,AVX 7800,AVX 9800,AVX 9800 6VS,AVX 7600,AVX 10650",
        "sub_product": "vAPV,vxAG,vASF,vAMP,ZTAG,Struxture Inmotion,Struxture Endpoint",
        "solution": "SLB,LLB,GSLB,SSLI,SSLO,L3 VPN,L4 VPN,SSL VPN,DD,WAF,DDOS"
    },
    {
        "product": "APV",
        "platform": "APV 1900,APV 2900,APV 5900,APV 7900,APV 9900,APV 10900,APV 1800,APV 2800,APV 5800,APV 7800,APV 9800",
        "sub_product": "H/W,S/W",
        "solution": "SLB,LLB,GSLB,SSLI,SSLO"
    },
    {
        "product": "vAPV",
        "platform": "VMware,Nutanix,RHVP",
        "sub_product": "",
        "solution": "SLB,LLB,GSLB,SSLI,SSLO"
    },
    {
        "product": "AG",
        "platform": "AG 1000 vS,AG 1100 vS,AG 1200 vS,AG 1500 vS,AG 1500 FIPS,AG 1600 vS",
        "sub_product": "H/W,S/W",
        "solution": "L3 VPN,L4 VPN,SSL VPN,DD"
    },
    {
        "product": "vxAG",
        "platform": "VMware,Nutanix,RHVP",
        "sub_product": "",
        "solution": "L3 VPN,L4 VPN,SSL VPN,DD"
    },
    {
        "product": "ASF",
        "platform": "ASF 1800,ASF 2800,ASF 5800,VMware,Nutanix,RHVP",
        "sub_product": "H/W,S/W",
        "solution": "WAF,DDOS"
    }
]

def seed_taxonomy():
    db = SessionLocal()
    try:
        for data in TAXONOMY_DATA:
            existing = db.query(ProductTaxonomy).filter(ProductTaxonomy.product == data["product"]).first()
            if not existing:
                new_tax = ProductTaxonomy(**data)
                db.add(new_tax)
                print(f"Seeded taxonomy for: {data['product']}")
            else:
                existing.platform = data["platform"]
                existing.sub_product = data["sub_product"]
                existing.solution = data["solution"]
                print(f"Updated taxonomy for: {data['product']}")
        db.commit()
    except Exception as e:
        print(f"Error seeding taxonomy: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_taxonomy()
