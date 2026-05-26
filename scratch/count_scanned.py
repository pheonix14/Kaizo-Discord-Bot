import sys
sys.path.append(".")
import logger

def check_data():
    print("Checking scanned_users:")
    res_users = logger._sb.table("scanned_users").select("*").execute()
    print(f"Total scanned users: {len(res_users.data)}")
    for user in res_users.data[:10]:
        print(f"  ID: {user['id']} | Username: {user['username']} | Status: {user['status']} | Bio: {user['bio']} | Custom Status: {user['custom_status']}")
        
    print("\nChecking scanned_members:")
    res_members = logger._sb.table("scanned_members").select("*").execute()
    print(f"Total scanned members: {len(res_members.data)}")
    for member in res_members.data[:10]:
        print(f"  ID: {member['id']} | Guild ID: {member['guild_id']} | User ID: {member['user_id']} | Nickname: {member['nickname']} | Joined At: {member['joined_at']}")

if __name__ == "__main__":
    check_data()
