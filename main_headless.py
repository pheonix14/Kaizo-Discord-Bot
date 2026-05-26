import threading
import engine
import logger
from keep_alive import keep_alive

if __name__ == "__main__":
    print("[System] Starting Fafnir Engine in Headless Mode...")
    # Initialize DB if not exists
    logger.init_db()
    
    # Start the automation engine in background (already non-blocking now)
    engine.start()
    
    # Start web server for GUI in MAIN thread (Blocking)
    from keep_alive import run_flask
    run_flask()
