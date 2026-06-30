import urllib.request
import urllib.parse
import json

def test_login():
    url = "http://localhost:8000/auth/login"
    data = urllib.parse.urlencode({
        "username": "superadmin",
        "password": "Admin@123"
    }).encode()
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode())
                print("Login successful!")
                print(f"Token: {res_data.get('access_token')[:20]}...")
            else:
                print(f"Login failed: {response.status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
