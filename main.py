import socket
import warnings

# Monkey-patch socket.getaddrinfo to force IPv4 DNS resolution (prevents IPv6 getaddrinfo failed errors on Windows)
_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(*args, **kwargs):
    args = list(args)
    if 'family' in kwargs:
        kwargs['family'] = socket.AF_INET
    elif len(args) >= 3:
        args[2] = socket.AF_INET
    else:
        while len(args) < 3:
            args.append(0)
        args[2] = socket.AF_INET
    return _original_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

# Ignore RequestsDependencyWarning related to urllib3/chardet mismatch
warnings.filterwarnings("ignore", message=".*urllib3.*")

import asyncio
import logging
import uvicorn
import errno
import discord
from src import config
from src.bot.engine import bot
# Removed FastAPI server import; using Flask backend

class ColorFormatter(logging.Formatter):
    # ANSI color codes
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[36;20m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: cyan + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        # Apply specific colors to specific categories if desired
        if record.levelno == logging.INFO:
            if "discord" in record.name:
                log_fmt = self.blue + self.format_str + self.reset
            elif "kaizer" in record.name:
                log_fmt = self.green + self.format_str + self.reset

        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
root_logger.addHandler(handler)
logger = logging.getLogger("kaizer_k5.main")

def run_web():
    """Start the Flask Web Server using the Flask app defined in src.web.flask_app."""
    from src.web.flask_app import app as flask_app
    host = config.HOST
    port = config.PORT
    logger.info(f"Starting Flask Dashboard on http://{host}:{port}")
    # Flask's built‑in server is sufficient for development; for production consider a WSGI server.
    flask_app.run(host=host, port=port, debug=False)


async def run_bot():
    """Start the Discord Bot client with automatic reconnect/retry logic."""
    logger.info("Initializing Discord Bot Client...")
    retry_delay = 5
    max_delay = 60
    try:
        while True:
            try:
                await bot.start(config.DISCORD_BOT_TOKEN)
                break
            except discord.errors.LoginFailure:
                logger.critical("Failed to log in: Invalid Discord Bot Token.")
                break
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Discord Bot encountered a startup exception: {e}")
                try:
                    await bot.close()
                except Exception as close_err:
                    logger.warning(f"Failed to close bot client during cleanup: {close_err}")
                logger.info(f"Retrying connection in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    finally:
        logger.info("Shutting down Discord Bot Client...")
        try:
            await asyncio.shield(bot.close())
        except Exception as e:
            logger.warning(f"Error closing bot in finally block: {e}")


async def main():
    # Run the web server and bot client concurrently, cleanly shutting down if either stops
    web_task = asyncio.create_task(asyncio.to_thread(run_web))
    bot_task = asyncio.create_task(run_bot())
    
    try:
        done, pending = await asyncio.wait(
            [web_task, bot_task],
            return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        # Clean up all pending tasks
        logger.info("Main loop exited. Starting cleanup...")
        pending_tasks = []
        for t in [web_task, bot_task]:
            if not t.done():
                pending_tasks.append(t)
                t.cancel()
        
        if pending_tasks:
            logger.info(f"Cancelling {len(pending_tasks)} pending tasks...")
            await asyncio.gather(*pending_tasks, return_exceptions=True)
            
        logger.info("Ensuring Discord Bot is cleanly closed...")
        try:
            await bot.close()
        except Exception as e:
            logger.warning(f"Error closing bot in main cleanup: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Project Kaizer K5 shutting down...")
