import os
import sys
import time
import webbrowser
import threading
import socket

# Ensure Windows terminal doesn't crash on print
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(base_dir, "New folder")
    os.chdir(app_dir)
    sys.path.insert(0, app_dir)

    local_ip = get_local_ip()

    threading.Thread(target=open_browser, daemon=True).start()
    
    import uvicorn
    print("=" * 65)
    print("  VRIXA AI ASSISTANT - STARK HUD ONLINE")
    print("  HARSH - ROLL NO. 23035004049")
    print("-" * 65)
    print("  LAPTOP / PC LINK : http://127.0.0.1:8000")
    print(f"  PHONE LINK (Same Wi-Fi): http://{local_ip}:8000")
    print("=" * 65)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
