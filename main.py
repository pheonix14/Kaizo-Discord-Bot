import os
import sys
import subprocess
import webbrowser

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_kaizer_x():
    """
    Main entry point for KAIZER X.
    This launches the Dashboard which manages all bot instances.
    """
    print("====================================")
    print("\033[94m[PROCESS] STARTING KAIZER X SYSTEM\033[0m")
    print("\033[96m[STATUS]  Initializing Tactical OS...\033[0m")
    print("")
    print("\033[1;91m[ADMIN COMMAND CENTER (RESTRICTED)]\033[0m")
    print("\033[91m > http://localhost:5000/kaizer-gate\033[0m")
    print("")
    print("\033[1;92m[PUBLIC INFRASTRUCTURE (AUTO-OPENING)]\033[0m")
    print("\033[92m > http://localhost:3000/\033[0m")
    print("====================================")
    
    # Auto-open the homepage
    try:
        webbrowser.open("http://localhost:3000/")
    except Exception as e:
        print(f"\033[93m[WARNING] Could not auto-open browser: {e}\033[0m")
    
    dashboard_path = os.path.join("dashboard", "app.py")
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    
    if not os.path.exists(dashboard_path):
        print(f"[ERROR] Could not find {dashboard_path}!")
        return

    processes = []
    
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Start the Next.js Frontend in the background
        print("\033[96m[SYSTEM] Launching Frontend (Next.js)...\033[0m")
        if os.path.exists(web_dir):
            # Using shell=True for npm commands on Windows is usually safer
            frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd=web_dir, shell=True)
            processes.append(frontend_process)
        else:
            print("\033[93m[WARNING] 'web' directory not found. Frontend will not start.\033[0m")

        # Start the Quart Dashboard (foreground)
        print("\033[96m[SYSTEM] Launching Backend (Quart)...\033[0m")
        subprocess.run([sys.executable, dashboard_path], cwd=project_root)

    except KeyboardInterrupt:
        print("\n\033[91m[PROCESS] KAIZER X System shutting down...\033[0m")
        for p in processes:
            p.terminate()
    except Exception as e:
        print(f"[ERROR] System failed to start: {e}")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    start_kaizer_x()
