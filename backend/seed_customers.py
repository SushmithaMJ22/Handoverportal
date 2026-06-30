from database import SessionLocal
from models import Customer

SAMPLE_CUSTOMERS = [
    {
        "name": "Acme Corporation",
        "contact_person": "John Smith",
        "phone": "+1-555-0101",
        "email": "john@acme.com",
        "region": "North America"
    },
    {
        "name": "Gulf Tech Solutions",
        "contact_person": "Ahmed Al-Rashid",
        "phone": "+971-50-123456",
        "email": "ahmed@gulftech.ae",
        "region": "Middle East"
    },
    {
        "name": "Asia Pacific Networks",
        "contact_person": "Li Wei",
        "phone": "+65-9123-4567",
        "email": "liwei@apnetworks.sg",
        "region": "Southeast Asia"
    },
    {
        "name": "Euro Systems GmbH",
        "contact_person": "Klaus Weber",
        "phone": "+49-89-123456",
        "email": "k.weber@eurosys.de",
        "region": "Europe"
    }
]

def seed_customers():
    db = SessionLocal()
    try:
        for data in SAMPLE_CUSTOMERS:
            existing = db.query(Customer).filter(Customer.name == data["name"]).first()
            if not existing:
                new_customer = Customer(**data)
                db.add(new_customer)
                print(f"Seeded customer: {data['name']}")
            else:
                print(f"Customer already exists: {data['name']}")
        db.commit()
    except Exception as e:
        print(f"Error seeding customers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_customers()
