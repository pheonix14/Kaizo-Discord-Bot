import sys
sys.path.append(".")
import engine
import logger
import time

def print_sessions():
    print("Checking live node sessions:")
    for tid in [t["id"] for t in logger.get_tokens()]:
        node = engine.get_node(tid)
        if node:
            session = node.bot.gateway.session
            print(f"\nNode label: {node.label}")
            print(f"  Session ID (hex): {hex(id(session))}")
            print(f"  Connected: {node.bot.gateway.connected}")
            print(f"  READY Flag: {node.bot.gateway.READY}")
            try:
                print(f"  _settings_ready type: {type(session._settings_ready)}")
                print(f"  _settings_ready keys: {list(session._settings_ready.keys())[:10]}")
                print(f"  _settings_ready_supp keys: {list(session._settings_ready_supp.keys())[:10]}")
            except Exception as e:
                print(f"  Error reading fields: {e}")
        else:
            print(f"Node {tid[:8]}... is not active in engine.")

if __name__ == "__main__":
    print_sessions()
