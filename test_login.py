import requests
import json

def test_login():
    url = "http://127.0.0.1:8000/token"
    username = "testuser123"
    password = "password123"
    
    # For the /token endpoint, we need to use form data, not JSON
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Sending login request to {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    # Note: the token endpoint expects form data, not JSON
    response = requests.post(url, data=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("Login successful!")
        token_data = response.json()
        print(f"Token: {token_data['access_token']}")
        
        # Save token to file
        with open("auth_token.json", "w") as f:
            json.dump({
                "username": username,
                "password": password,
                "token": token_data["access_token"],
                "token_type": token_data["token_type"]
            }, f)
        print("Token saved to auth_token.json")
    else:
        print("Login failed.")
        
if __name__ == "__main__":
    test_login() 