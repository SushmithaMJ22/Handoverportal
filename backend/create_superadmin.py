from database import SessionLocal
from models import User, UserRole
from core.security import get_password_hash

def create_superadmin():
    db = SessionLocal()
    try:
        # Check if superadmin already exists
        user = db.query(User).filter(User.username == "superadmin").first()
        if user:
            print("Superadmin user already exists.")
            return

        # Create superadmin user
        hashed_password = get_password_hash("Admin@123")
        superadmin = User(
            username="superadmin",
            email="admin@company.com",
            hashed_password=hashed_password,
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        print("Superadmin user created successfully!")
        print("Credentials: superadmin / Admin@123")
    except Exception as e:
        print(f"Error creating superadmin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_superadmin()
