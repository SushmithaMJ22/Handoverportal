
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def verify_free_text_handovers():
    # 1. Login
    login_data = {
        "username": "superadmin",
        "password": "Admin@123"
    }
    print("Logging in...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Create handover with free-text fields
    print("Creating handover with free-text customer fields...")
    handover_payload = {
        "customer_name": "Gulf Tech Solutions",
        "region": "Middle East",
        "contact_person": "Ahmed Hassan",
        "contact_phone": "+971-50-1234567",
        "contact_email": "ahmed@gulftech.ae",
        "ps_engineer": "FreeText Tester",
        "product": "APV",
        "platform": "APV 1900",
        "remarks": "Testing free-text implementation",
        "status": "active"
    }
    
    ho_res = requests.post(f"{BASE_URL}/handovers/", json=handover_payload, headers=headers)
    if ho_res.status_code == 200:
        created_ho = ho_res.json()
        print(f"Handover created with ID: {created_ho['id']}")
        print(f"Customer Name: {created_ho.get('customer_name')}")
        print(f"Region: {created_ho.get('region')}")
    else:
        print(f"Failed to create handover: {ho_res.text}")
        return

    # 3. Verify in list
    print("\nVerifying in list...")
    list_res = requests.get(f"{BASE_URL}/handovers", headers=headers)
    handovers = list_res.json()
    test_ho = next((h for h in handovers if h['id'] == created_ho['id']), None)
    if test_ho:
        print(f"List entry customer_name: {test_ho.get('customer_name')}")
        print(f"List entry region: {test_ho.get('region')}")
    else:
        print("Error: Handover not found in list.")

    # 4. Verify in detail
    print("\nVerifying in detail...")
    detail_res = requests.get(f"{BASE_URL}/handovers/{created_ho['id']}", headers=headers)
    detail_ho = detail_res.json()
    print(f"Detail customer_name: {detail_ho.get('customer_name')}")
    print(f"Detail region: {detail_ho.get('region')}")
    print(f"Detail contact_person: {detail_ho.get('contact_person')}")

    # 5. Verify dashboard stats
    print("\nVerifying dashboard stats...")
    stats_res = requests.get(f"{BASE_URL}/handovers/stats/dashboard", headers=headers)
    stats = stats_res.json()
    recent_ho = next((h for h in stats['recent_handovers'] if h['id'] == created_ho['id']), None)
    if recent_ho:
        print(f"Dashboard recent handover customer_name: {recent_ho.get('customer_name')}")
    else:
        print("Error: Handover not found in dashboard recent list.")

if __name__ == "__main__":
    verify_free_text_handovers()
