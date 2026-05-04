import os
import sys
import subprocess

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_kaizer_x():
    """
    Main entry point for KAIZER X.
    This launches the Dashboard which manages all bot instances.
    """
    print("====================================")
    print("[PROCESS] STARTING KAIZER X SYSTEM")
    print("[PROCESS] Initializing Admin Controller...")
    print("====================================")
    
    dashboard_path = os.path.join("dashboard", "app.py")
    
    if not os.path.exists(dashboard_path):
        print(f"[ERROR] Could not find {dashboard_path}!")
        return

    # Start the dashboard
    # We use sys.executable and specify the CWD to ensure absolute path reliability
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, dashboard_path], cwd=project_root)

    except KeyboardInterrupt:
        print("\n[PROCESS] KAIZER X System shutting down...")
    except Exception as e:
        print(f"[ERROR] System failed to start: {e}")

if __name__ == "__main__":
    start_kaizer_x()
