from database import SessionLocal 
from models import User, UserRole 
from core.security import get_password_hash, verify_password 
 
db = SessionLocal() 
 
# List all users 
print("=== ALL USERS ===") 
users = db.query(User).all() 
for u in users: 
    print(f"ID: {u.id} | Username: [{u.username}] | Role: {u.role} | Active: {u.is_active}") 
 
print("\n=== RESETTING PASSWORDS ===") 
# Reset password for ALL non-superadmin users to Test@1234 
for u in users: 
    if u.role != UserRole.SUPER_ADMIN: 
        u.hashed_password = get_password_hash('Test@1234') 
        u.is_active = True 
        print(f"Reset: {u.username} -> password is now Test@1234") 
    else: 
        u.hashed_password = get_password_hash('Admin@123') 
        u.is_active = True 
        print(f"Reset: {u.username} -> password is now Admin@123") 
 
db.commit() 
print("\n=== VERIFY PASSWORDS ===") 
users = db.query(User).all() 
for u in users: 
    if u.role != UserRole.SUPER_ADMIN: 
        valid = verify_password('Test@1234', u.hashed_password) 
    else: 
        valid = verify_password('Admin@123', u.hashed_password) 
    print(f"{u.username}: password valid = {valid}") 
 
db.close() 
print("\nDone! Try logging in now.") 
