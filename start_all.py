import subprocess
import sys
import time
import webbrowser
import os
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    print("🚀 Starting Auto_VAPT Professional (Local Mode)...")
    print("---------------------------------------------------------")

    # 1. Start Backend
    print("[*] Starting Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=os.getcwd(),
        shell=True
    )

    # 2. Start Frontend
    print("[*] Starting Frontend (Vite)...")
    frontend_cwd = os.path.join(os.getcwd(), "frontend")
    # Check if node_modules exists, offer to install if missing
    if not os.path.exists(os.path.join(frontend_cwd, "node_modules")):
        print("⚠️ node_modules not found. Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_cwd, shell=True)

    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_cwd,
        shell=True
    )

    print("\n✅ Services started!")
    print("---------------------------------------------------------")
    print("🌐 Dashboard: http://localhost:5173")
    print("📁 API:       http://localhost:8000")
    print("---------------------------------------------------------")

    try:
        time.sleep(5) # Wait for things to boot
        webbrowser.open("http://localhost:5173")
        print("[*] Press Ctrl+C to stop servers...")
        
        # Keep alive
        while True:
            time.sleep(1)
            if backend_process.poll() is not None or frontend_process.poll() is not None:
                print("⚠️ One of the services exited unexpectedy.")
                break
                
    except KeyboardInterrupt:
        print("\n[*] Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        # Force kill on Windows if needed
        os.system("taskkill /F /IM uvicorn.exe /T")
        os.system("taskkill /F /IM node.exe /T")
        
if __name__ == "__main__":
    main()
