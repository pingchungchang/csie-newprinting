import requests
import json

BASE_URL = "http://localhost:8001/api"
USERNAME = "testuser" 
PASSWORD = "test1234"

def run_test():
    session = requests.Session()
    
    # 1. Login
    print(f">>> 1. Attempting login as {USERNAME}")
    res = session.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
    print("Login Status:", res.status_code, res.text)
    if res.status_code != 200:
        print("Login failed.")
        return

    # extract CSRF token after login
    csrf_token = session.cookies.get('csrftoken')
    
    # insert token into header
    headers = {
        "X-CSRFToken": csrf_token
    }

    # 2. upload PDF to print (require CSRF)
    print("\n>>> 2. Uploading dummy_5m.pdf...")
    try:
        with open("dummy_5m.pdf", "rb") as f:
            files = [('files', ('dummy_5m.pdf', f, 'application/pdf'))]
            data = {'duplex': 'True'}
            
            res = session.post(f"{BASE_URL}/print", files=files, data=data, headers=headers)
            
        print("Print Status:", res.status_code)
        try:
            print("Print Response:", json.dumps(res.json(), indent=2, ensure_ascii=False))
        except:
            print("Print Response (Raw):", res.text)
            
    except FileNotFoundError:
        print("File' dummy_5m.pdf' not found!")

if __name__ == "__main__":
    run_test()
