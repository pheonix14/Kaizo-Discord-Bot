import webbrowser, threading, time, os, subprocess, sys, io
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from keep_alive import keep_alive
import engine

if __name__ == "__main__":
    import logger
    logger.init_db()
    logger.set_status(f"Online (PID {os.getpid()})")
    
    # 1. Start Engine in background
    engine.start()

    # 2. Start Pokémon image downloader in background
    def download_task():
        poke_dir = os.path.join("static", "pokemon")
        if not os.path.exists(poke_dir) or len(os.listdir(poke_dir)) < 100:
            logger.log_event("Pokémon images missing or incomplete. Starting background download...", "info")
            try:
                subprocess.run([sys.executable, "download_pokemon.py"])
                logger.log_event("Background Pokémon image download complete.", "success")
            except Exception as e:
                logger.log_event(f"Background download failed: {e}", "error")
    threading.Thread(target=download_task, daemon=True, name="ImageDownloader").start()

    # 3. Optional: Open browser only if local
    if "RENDER" not in os.environ:
        def _open():
            time.sleep(2)
            port = int(os.environ.get("PORT", 8085))
            webbrowser.open(f"http://127.0.0.1:{port}")
        threading.Thread(target=_open, daemon=True).start()

    # 4. Start Flask in MAIN thread (Blocking)
    from keep_alive import run_flask
    run_flask()
