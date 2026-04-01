import sys
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Determine Python Executable path
VENV_PYTHON = os.path.join(".venv", "Scripts", "python.exe")
if os.path.exists(VENV_PYTHON):
    PYTHON_BIN = VENV_PYTHON
else:
    PYTHON_BIN = sys.executable

class KaizerChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.last_restart = 0
        self.start_process()

    def start_process(self):
        # Prevent double restarts from rapid events
        now = time.time()
        if now - self.last_restart < 1.0:
            return
        self.last_restart = now

        # Clean up existing running process
        if self.process:
            print("==================================================")
            print("[CHANGE] File change detected! Restarting Kaizo...")
            print("==================================================")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        else:
            print("==================================================")
            print("[SYSTEM] Starting Kaizo Security Node in watch mode...")
            print("==================================================")

        # Launch main.py
        try:
            env = os.environ.copy()
            env["KAIZER_WATCHDOG"] = "1"
            self.process = subprocess.Popen([PYTHON_BIN, "main.py"], env=env, stdin=sys.stdin)
        except Exception as e:
            print(f"[ERROR] Failed to launch main.py: {e}")

    def on_any_event(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        
        # Ignored paths and formats
        ignore_keywords = [".venv", ".git", "__pycache__", ".idea", ".vscode", "test_supabase.py", "node_modules", "logs", "database", ".gemini"]
        if any(kw in filepath for kw in ignore_keywords):
            return

        # Extensions to watch
        valid_extensions = ['.py', '.html', '.css', '.js', '.sql', '.env']
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in valid_extensions:
            self.start_process()

if __name__ == "__main__":
    handler = KaizerChangeHandler()
    
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Stopping Kaizo watch observer...")
        observer.stop()
        if handler.process:
            handler.process.terminate()
            try:
                handler.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                handler.process.kill()
    observer.join()
