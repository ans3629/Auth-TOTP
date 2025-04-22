# Screen Capture Malware Testing Environment

This repository contains a demonstration environment for testing screen capture malware capabilities. The setup includes three virtual machines configured to demonstrate how screen capture malware can be deployed, executed, and used to intercept sensitive information such as TOTP codes.

## ⚠️ WARNING

This code is for **EDUCATIONAL PURPOSES ONLY**. The malware demonstration tools included in this repository should ONLY be used in isolated test environments. Unauthorized use against systems or individuals is illegal and unethical.

https://github.com/user-attachments/assets/4650ad2a-feec-4b45-9008-5097396e1bc0

## Environment Setup

### Required Components

- 3 Virtual Machines:
  - **Client VM** (Windows): The target machine
  - **Server VM** (Windows): Runs the legitimate server application
  - **Attacker VM** (Windows): Runs the malicious code to intercept data

### VM Configuration

#### 1. Network Configuration

Ensure all VMs are on the same network and can communicate with each other:

- Use NAT or Host-only networking in your virtualization software
- Configure static IP addresses for easier setup
- Test connectivity with ping between all machines

#### 2. Security Configuration

For testing purposes only, disable security features:

- Disable Windows Defender or other antivirus software on all machines
- Disable Windows Firewall on all machines
- Add exceptions for all Python scripts in any security software

```
# Disable Windows Defender Real-time protection (PowerShell as Administrator)
Set-MpPreference -DisableRealtimeMonitoring $true

# Disable Windows Firewall (PowerShell as Administrator)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
```

#### 3. Software Requirements

Install the following on all machines:

- Python 3.8+ (Add to PATH during installation)
- Required Python packages:

```
pip install numpy opencv-python pillow pywin32 colorama
```

## Setup Instructions

### Client VM (Target) Setup

1. Copy the following files to the Client VM:
   - `client.py` - Legitimate client application
   - `login_client.py` - Application that uses TOTP for authentication
   - `notascreenshare.py` - The malware that captures screenshots

2. Configure the malware:
   - Open `notascreenshare.py` and update the following:
     ```python
     ATTACKER_IP = "x.x.x.x"  # Replace with the Attacker VM's IP address
     ```

3. Run the legitimate applications:
   ```
   python client.py
   python login_client.py
   ```

4. Run the malware (in a separate console, or configured to run at startup):
   ```
   python notascreenshare.py
   ```

### Server VM Setup

1. Copy `server.py` to the Server VM.

2. Start the server:
   ```
   python server.py
   ```

### Attacker VM Setup

1. Copy the following files to the Attacker VM:
   - `screen_intercept.py` - The script that receives screenshots
   - `login_client.py` - Used to log in with intercepted TOTP codes

2. Run the screen intercept script:
   ```
   python screen_intercept.py
   ```

3. When TOTP codes are intercepted, you can use `login_client.py` to attempt authentication:
   ```
   python login_client.py
   ```

## Testing the Environment

1. On the Client VM:
   - Log in to the legitimate application using `login_client.py`
   - The TOTP code will be displayed on the screen
   - The malware (`notascreenshare.py`) will capture this screen

2. On the Attacker VM:
   - `screen_intercept.py` receives the screenshots
   - Observe the TOTP code in the intercepted screenshots
   - Use `login_client.py` with the intercepted code to gain unauthorized access

## Understanding the Code

### notascreenshare.py (Malware)

This is the malicious software that:
- Takes screenshots of the target machine
- Streams live screen content to the attacker
- Records video of the screen activity
- Runs silently in the background with a misleading name

### screen_intercept.py (Attacker Tool)

This software runs on the attacker's machine and:
- Receives screenshots and videos from the infected client
- Provides a UI to view, save, and manage the captured data
- Allows live viewing of the target's screen

## Additional Notes

- The malware is designed to look like a system process to avoid detection
- It creates a hidden directory for temporary files
- It attempts to reconnect if the connection is lost
- Use Task Manager to end the malware process after testing

## Troubleshooting

- **Connection Issues**: Ensure all firewalls are disabled and all machines can ping each other
- **Missing Dependencies**: Make sure all required Python packages are installed
- **Display Issues**: If OpenCV windows don't display properly, try updating graphics drivers

## Cleaning Up

After testing, ensure you:
1. Terminate all Python processes
2. Delete all captured data
3. Restore security settings on all machines
