import requests
import time

SERVER_URL = "http://localhost:5000/get-totp"
USERNAME = "alice"

def get_code():
    try:
        response = requests.get(SERVER_URL, params={'user': USERNAME})
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

while True:
    code = get_code()
    if code:
        print(f"[Client] Received TOTP: {code}")
    time.sleep(5)

