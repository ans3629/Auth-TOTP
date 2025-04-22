TOTP SERVER SCRIPT - README
===========================

This script is a simple TOTP (Time-Based One-Time Password) server implemented using Flask. It generates TOTP codes for a specific user and allows login attempts by verifying the TOTP code against the server's shared secret.

======================================================================
DISCLAIMER
======================================================================
This server script is for educational use only.
Do NOT deploy this server in production or expose it to the internet 
without proper security mechanisms like rate limiting and encryption.

======================================================================
SCRIPT: totp_server.py
======================================================================

DESCRIPTION:
------------
- A Flask-based server that generates a TOTP code for a given user.
- Verifies the TOTP code during login attempts.
- Responds with either a success or failure message based on the TOTP verification.

TECHNOLOGIES USED:
------------------
- Python 3
- Flask web framework
- pyotp library for generating and verifying TOTP codes

DEPENDENCIES:
-------------
Install using pip:

    pip install Flask pyotp

======================================================================
USAGE
======================================================================

1. Run the server:

    python totp_server.py

   The server will start listening on `http://0.0.0.0:5000`.

2. The server exposes two endpoints:

    - `/get-totp?user=<username>` - Returns the current TOTP code for the given user.
    - `/login?user=<username>&code=<totp_code>` - Verifies the provided TOTP code for the user.

======================================================================
CONFIGURATION
======================================================================

Inside the script, you can configure:

- `shared_secret` – The static shared secret used for TOTP generation (currently random for demo purposes).
- `totp = pyotp.TOTP(shared_secret, digits=4)` – Configures the TOTP generator to use 4-digit codes (you can modify this for longer codes).

======================================================================
ENDPOINTS
======================================================================

1. **/get-totp**

    Example Request:
        GET http://localhost:5000/get-totp?user=alice

    Example Response:
        539102

    - Generates a new TOTP code for the specified user.
    - Returns the code as a plain text response.

2. **/login**

    Example Request:
        GET http://localhost:5000/login?user=alice&code=539102

    Example Response:
        Login successful

    - Verifies the provided TOTP code for the specified user.
    - Returns "Login successful" or "Login failed" based on verification.

======================================================================
EXAMPLE OUTPUT (Server Logs)
======================================================================

[Server] Generated TOTP for alice: 539102
[Server] SUCCESSFUL login for alice using code: 539102
...

======================================================================
SECURITY NOTES
======================================================================

- **Shared Secret**: The shared secret used for generating TOTP codes is static in this demo. In real-world implementations, this secret should be securely shared and stored (e.g., using environment variables, hardware tokens, or encrypted databases).
- **No rate limiting**: There is no rate-limiting or protection against brute-force attacks on login attempts.
- **No HTTPS**: Communication is in plain HTTP. For production, HTTPS is highly recommended to protect sensitive data in transit.

======================================================================
AUTHOR
======================================================================

Created for educational demonstration of TOTP vulnerabilities.
Author: [Your Name]

