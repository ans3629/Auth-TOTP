# Auth-TOTP
TOTP CLIENT-SERVER SETUP - README
=================================

This setup demonstrates the client-server communication for TOTP (Time-Based One-Time Password) authentication. The server generates TOTP codes for a given user, while the client requests and uses those codes to attempt a login. The setup is intentionally vulnerable to demonstrate common security flaws in TOTP systems.

This setup consists of three scripts:
1. **TOTP Server** (`totp_server.py`) - Generates and verifies TOTP codes.
2. **TOTP Client** (`totp_client.py`) - Retrieves and prints TOTP codes for a specified user.
3. **Login Script** (`login.py`) - Submits TOTP codes to the server for login attempts.


DISCLAIMER
----------
This system is for educational use only. 
Do NOT deploy or expose this setup in a production environment without proper security mechanisms. This setup demonstrates vulnerabilities in TOTP systems for educational purposes and ethical hacking.


REQUIREMENTS
----------
- Python 3.x
- Install dependencies using pip:

    pip install Flask pyotp requests tqdm


FILES IN THIS SETUP
----------

1. **totp_server.py**:
    - A Flask-based server that generates TOTP codes and verifies them for login attempts.
    - Exposes two endpoints:
      - `/get-totp?user=<username>` – Returns the current TOTP code for the user.
      - `/login?user=<username>&code=<totp_code>` – Verifies the provided TOTP code for the user.

2. **totp_client.py**:
    - A client that repeatedly requests a TOTP code from the server.
    - Polls the server every 5 seconds and prints the received TOTP code.

3. **login.py**:
    - A simple script that submits a TOTP code for login verification to the server.
    - Requires manual input of the TOTP code.


HOW TO RUN THE SETUP
----------

1. **Run the Server**:
    - Start the server by running the following command:

        python totp_server.py

    - The server will be accessible on `http://localhost:5000`.

2. **Run the Client**:
    - Run the client to start polling for TOTP codes:

        python totp_client.py

    - The client will display the TOTP codes received from the server.

3. **Run the Login Script**:
    - After receiving a TOTP code from the client, manually enter it into the login script for login attempts:

        python login.py

    - Enter the TOTP code when prompted.


VULNERABILITIES DEMONSTRATED
----------

This TOTP setup is vulnerable to the following common attacks:

1. **Brute Force Attack**:
    - The TOTP system is susceptible to brute-force attacks due to the lack of rate-limiting. An attacker can try all possible 4-digit codes (0000–9999) without any protection or lockouts.
    - The `brute_force_http.py` script demonstrates an attacker sending all possible TOTP codes to the server to guess the correct one.

2. **No Rate Limiting on Login Attempts**:
    - The server does not implement any rate-limiting or account lockout mechanism after failed login attempts. This makes it easier for attackers to keep trying different codes without any restriction.

3. **Transmission of TOTP Codes Over HTTP**:
    - The communication between the client and server occurs over HTTP, which is not secure. This exposes the TOTP codes to eavesdropping, allowing attackers to capture sensitive information during transmission.
    - For production systems, **HTTPS** should be used to encrypt all communication.


CONFIGURATION
----------

In the server script (`totp_server.py`), you can configure:

- `shared_secret` – The shared secret used to generate the TOTP codes (currently randomly generated for the demo).
- `totp = pyotp.TOTP(shared_secret, digits=4)` – Configures the TOTP generator to use 4-digit codes (this can be changed to use longer codes if needed).

In the client script (`totp_client.py`), you can configure:

- `SERVER_URL` – The URL of the server providing the TOTP codes. Modify it if the server is running on a different machine or port.
- `USERNAME` – The username to request TOTP codes for (default is "alice").

In the login script (`login.py`), the user can input the TOTP code that is manually retrieved from the client.


EXAMPLE OUTPUT
----------

**Server logs** (on successful login):

[Server] Generated TOTP for alice: 539102
[Server] SUCCESSFUL login for alice using code: 539102

**Client output** (receiving TOTP):

[Client] Received TOTP: 539102
[Client] Received TOTP: 539102

**Login script output**:

Enter the TOTP code: 539102
[Client] Server responded: Login successful


SECURITY NOTES
----------
This setup is deliberately insecure to demonstrate vulnerabilities in a basic TOTP implementation. For real-world systems, consider the following improvements:

- **Use HTTPS**: Always use HTTPS to prevent MITM (Man-In-The-Middle) attacks and protect sensitive data in transit.
- **Rate Limiting**: Implement rate limiting and account lockouts after a set number of failed login attempts to mitigate brute-force attacks.
- **Use Stronger Secrets**: Use securely generated and stored shared secrets for TOTP, rather than hardcoded or easily guessable ones.
  
Created for educational demonstration of TOTP vulnerabilities.

