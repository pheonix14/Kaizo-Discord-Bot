import engine
import sys

node = engine.get_node("0133a63e-789e-4b0e-87ee-1a7181956439") # yokirahawa
if not node:
    print("yokirahawa node not found")
    sys.exit(1)

gw = node.bot.gateway
session = gw.session

print(f"yokirahawa Gateway info:")
print(f"  connected: {gw.connected}")
print(f"  ready: {gw.READY}")
print(f"  session_id: {gw.session_id}")
print(f"  sequence: {gw.sequence}")
print(f"  session type: {type(session)}")
print(f"  session._settings_ready class: {type(session._settings_ready)}")
print(f"  session._settings_ready values: {session._settings_ready}")
print(f"  session._settings_ready_supp values: {list(session._settings_ready_supp.keys()) if isinstance(session._settings_ready_supp, dict) else session._settings_ready_supp}")

# Check thread local mapping
import _thread
from discum.gateway.session import _thread_to_session
print(f"Current thread mapping count: {len(_thread_to_session)}")
print(f"Current thread mapping keys: {list(_thread_to_session.keys())}")
for t_id, s_obj in list(_thread_to_session.items()):
    print(f"  Thread {t_id} maps to session {id(s_obj)} (current session id={id(session)})")
