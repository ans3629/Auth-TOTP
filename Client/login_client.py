import requests

server_ip = 'http://192.168.81.147:5000'  # Replace with actual server IP
user = 'alice'

# Either hardcode the code (for screen recording demo)
# OR get a fresh one from the server
totp_code = input("Enter the TOTP code: ")

login_url = f"{server_ip}/login"
params = {'user': user, 'code': totp_code}

response = requests.get(login_url, params=params)
print(f"[Client] Server responded: {response.text}")

