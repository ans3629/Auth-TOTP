TOTP CLIENT SCRIPT - README
============================

This script is a simple TOTP client that regularly polls a server to retrieve the current one-time password (OTP) code for a specific user. It is designed for educational purposes in demonstrating the flow of TOTP code generation and client-server communication.


**DISCLAIMER**

This script is for educational use only.
Do NOT use or deploy this on any system you do not own or have explicit
permission to interact with.


SCRIPT: totp_client.py


DESCRIPTION:
------------
- Periodically sends a GET request to a TOTP-generating server endpoint.
- Requests a TOTP code for a specific user (e.g., "alice").
- Prints the received TOTP code to the console every 5 seconds.

TECHNOLOGIES USED:
------------------
- Python 3
- `requests` library for HTTP requests
- `time` module for polling delay

DEPENDENCIES:
-------------
Install using pip:

    pip install requests


**USAGE**


1. Make sure the TOTP server is running and accessible.

   Example server endpoint:
       http://localhost:5000/get-totp

2. Update the `SERVER_URL` if the server is running remotely:

    SERVER_URL = "http://<server-ip>:5000/get-totp"

3. Run the client:

    python totp_client.py


**HOW IT WORKS**


- The script repeatedly:
    - Sends a GET request to `/get-totp?user=alice`
    - Receives the current TOTP code as a plain text response
    - Prints the code with a timestamp (or every 5 seconds)
- It continues indefinitely until interrupted by the user (Ctrl+C)


**CONFIGURATION**


Inside the script, you can configure:

- `SERVER_URL` – Base URL of the server providing TOTP codes
- `USERNAME` – The target username (default is "alice")
- `time.sleep(5)` – Adjust the polling interval (currently 5 seconds)


**EXAMPLE OUTPUT**


[Client] Received TOTP: 539102
[Client] Received TOTP: 539102
[Client] Received TOTP: 812377
...


**NOTES**


- The server is expected to return a valid TOTP code as a plain text response.
- This client does not perform any validation or login attempt — it simply reads the current TOTP.
- Useful for testing or demonstrating code synchronization with a TOTP server.


**RELATED FILES**


- `server.py`          – The server that responds with TOTP codes
- `login.py`           – A script that submits the TOTP code for login
- `brute_force_http.py` – Demonstrates brute-forcing TOTP codes over HTTP

Created for educational demonstration of TOTP vulnerabilities.

