TOTP BRUTE-FORCING SCRIPT - README
==================================

This script performs a brute-force attack against a vulnerable TOTP login endpoint exposed over HTTP. It attempts all 4-digit TOTP codes (0000–9999) for a specified user until it receives a successful login response.


DISCLAIMER

This script is for educational purposes only.
Do NOT run this against any system you do not own or have explicit
permission to test.


SCRIPT: brute_force_http.py


DESCRIPTION:
------------
- Uses HTTP GET requests to brute-force a 4-digit TOTP code
- Targets a user account (`alice`) on a known login endpoint
- Stops on the first "Login successful" response

TECHNOLOGIES USED:
------------------
- Python 3
- `requests` for HTTP communication
- `tqdm` for progress display

DEPENDENCIES:
-------------
Install using pip:

    pip install requests tqdm


USAGE


1. Make sure the vulnerable TOTP server is running and accessible.

   Example server endpoint:
       http://192.168.81.147:5000/login

2. Run the brute-force script:

    python brute_force_http.py

   (Rename the file if needed to match your script name.)


CONFIGURATION


Inside the script, you can modify:

- `server_ip` – The IP and port of the vulnerable server
- `user` – The username being targeted
- `login_url` – Automatically formed from the server address

Example snippet:

    server_ip = 'http://192.168.81.147:5000'
    user = 'alice'
    login_url = f"{server_ip}/login"


HOW IT WORKS


- Generates 4-digit codes from 0000 to 9999
- Sends each code in an HTTP GET request to the login endpoint
    - Format: /login?user=alice&code=1234
- Monitors server responses
- On receiving "Login successful", prints the correct code and exits


OUTPUT EXAMPLE


Brute-forcing TOTP code:  43%|████████████████▍                  | 4321/10000 [00:06<00:08, 676.47it/s]

[+] SUCCESS! Code: 4321
Server Response: Login successful


VULNERABILITIES DEMONSTRATED


- No rate-limiting or lockout mechanisms on failed login attempts
- Predictable 4-digit code space
- Plain-text success response
- Use of HTTP (instead of HTTPS) exposes credentials in transit


CREDITS
Written as part of a client-server TOTP vulnerability demonstration.

