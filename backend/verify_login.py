
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def verify_login_flow():
    test_cases = [
        ("superadmin", "Admin@123", "super_admin"),
        ("mj", "Test@1234", "admin"),
        ("testuser", "Test@1234", "user")
    ]

    for username, password, expected_role in test_cases:
        print(f"\nTesting login for: {username} (expected role: {expected_role})")
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            # OAuth2 expects x-www-form-urlencoded
            res = requests.post(f"{BASE_URL}/auth/login", data=login_data)
            
            if res.status_code == 200:
                data = res.json()
                role = data['user']['role']
                print(f"Success! Role: {role}")
                if role == expected_role:
                    print("Role matches expected role.")
                else:
                    print(f"Role MISMATCH! Expected {expected_role}, got {role}")
            else:
                print(f"Login FAILED. Status: {res.status_code}")
                print(f"Detail: {res.text}")
        except Exception as e:
            print(f"Error during login test: {str(e)}")

if __name__ == "__main__":
    verify_login_flow()
