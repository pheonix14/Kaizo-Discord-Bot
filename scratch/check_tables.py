import sys
sys.path.append(".")
import logger

print("Connecting directly to Supabase via client...")
try:
    res = logger._sb.table("scanned_users").select("*").limit(1).execute()
    print("Success! Table 'scanned_users' is visible.")
    print("Data:", res.data)
except Exception as e:
    print("Failed to access 'scanned_users' table.")
    print("Exception Type:", type(e))
    print("Exception Details:", e)
