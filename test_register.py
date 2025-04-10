import requests
import json

def test_registration():
    url = "http://127.0.0.1:8000/register/user"
    username = "testuser123"
    password = "password123"
    
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Sending registration request to {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("Registration successful!")
    else:
        print("Registration failed.")
        
if __name__ == "__main__":
    test_registration() 