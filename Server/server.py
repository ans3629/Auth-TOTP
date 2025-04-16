from flask import Flask, request
import pyotp

app = Flask(__name__)

# Shared secret (static for demo purposes)
shared_secret = pyotp.random_base32()
totp = pyotp.TOTP(shared_secret, digits=4)

@app.route('/get-totp')
def get_totp():
    user = request.args.get('user')
    if not user:
        return "Missing user", 400
    code = totp.now()
    print(f"[Server] Generated TOTP for {user}: {code}\n")
    return code + "\n"

@app.route('/login')
def login():
    user = request.args.get('user')
    code = request.args.get('code')

    if not user or not code:
        return "Missing user or code", 400

    if totp.verify(code):
        print(f"[Server] SUCCESSFUL login for {user} using code: {code}")
        return "Login successful"
    else:
        print(f"[Server] FAILED login attempt for {user} using code: {code}")
        return "Login failed"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

