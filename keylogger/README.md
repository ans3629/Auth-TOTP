# TOTP Interception System

This repository contains a proof-of-concept system for intercepting Time-based One-Time Password (TOTP) codes. **For educational and security testing purposes only.**

## System Components

The system consists of three main components:

1. **Keylogger Client** - Runs on the target machine to capture keystrokes and clipboard data
2. **Attacker Listener** - Receives and processes intercepted TOTP codes
3. **Authentication Setup** - Existing TOTP authentication between client and server

## Network Configuration

Before running any components:

1. Ensure all machines can ping each other
2. Temporarily disable firewalls on all systems
3. Configure the correct IP addresses in the scripts

## Setup Instructions

### 1. Keylogger Client (Target Machine)

The keylogger disguises itself as a legitimate Windows Security Service and captures keystrokes, looking specifically for 4-digit TOTP codes.

**Configuration:**
- Edit `ATTACKER_IP` in the keylogger script to point to your attacker machine
- Default port is `4444` but can be modified if needed

**Execution:**
```
python totallynotakeylogger.py
```

The keylogger runs in the background with a system-like interface to avoid suspicion.

### 2. Attacker Listener (Attacker Machine)

The listener waits for connections from the keylogger client and captures any intercepted TOTP codes.

**Configuration:**
- By default, it listens on `0.0.0.0:4444` (all interfaces)
- Captured codes are stored in the `captured_codes` directory

**Execution:**
```
python totp_intercept.py
```

**Features:**
- Interactive menu system
- Live monitoring mode
- History of captured TOTP codes
- Sound alerts when codes are captured
- Export functionality

### 3. Authentication System

Your existing TOTP authentication system consists of:
- `login_client.py` - Authenticates with the server using TOTP
- `client.py` - Generates the TOTP codes
- `server.py` - Validates the TOTP codes

No modifications are needed for these components as they are already set up.

## Attack Flow

1. The keylogger runs on the target machine, monitoring for 4-digit patterns
2. When the user enters a TOTP code, the keylogger captures it
3. The keylogger sends the code to the attacker listener
4. The attacker listener receives and logs the code
5. The attacker can use the intercepted code within its validity window

## Warning

This tool is designed for educational purposes and legitimate security testing only. Unauthorized interception of authentication codes is illegal and unethical.

## Troubleshooting

- If connections fail, verify all IPs are correct and that firewalls are disabled
- Test connectivity using ping between all machines
- Check that port 4444 is not being used by other applications
- Ensure all machines are on the same network or can route to each other

## Requirements

- Python 3.6+
- Required Python modules:
  - pynput
  - socket
  - threading
  - colorama (optional, for better UI on the attacker side)
  - winsound (Windows-specific for sound alerts)
