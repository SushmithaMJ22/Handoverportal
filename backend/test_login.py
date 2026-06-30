import requests

def test_login():
    url = "http://localhost:8000/auth/login"
    data = {
        "username": "superadmin",
        "password": "Admin@123"
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Login successful!")
            print(f"Token: {response.json().get('access_token')[:20]}...")
        else:
            print(f"Login failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
