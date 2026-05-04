import pandas as pd
import os
import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths for our CSV databases
USERS_CSV = os.path.join(DB_DIR, 'users.csv')
SERVERS_CSV = os.path.join(DB_DIR, 'servers.csv')
WARNS_CSV = os.path.join(DB_DIR, 'warns.csv')
TICKETS_CSV = os.path.join(DB_DIR, 'tickets.csv')

def init_db():
    """
    Initializes the CSV databases if they do not exist using Pandas.
    """
    # Users Table
    if not os.path.exists(USERS_CSV):
        df_users = pd.DataFrame(columns=[
            'user_id', 'wallet', 'level', 'xp', 'premium', 'likes', 'skin'
        ])
        df_users.to_csv(USERS_CSV, index=False)
        print("[ DATABASE ] users.csv created.")

    # Servers Table
    if not os.path.exists(SERVERS_CSV):
        df_servers = pd.DataFrame(columns=[
            'server_id', 'prefix', 'theme', 'welcome_channel', 'premium_tier'
        ])
        df_servers.to_csv(SERVERS_CSV, index=False)
        print("[ DATABASE ] servers.csv created.")

    # Warnings Table
    if not os.path.exists(WARNS_CSV):
        df_warns = pd.DataFrame(columns=[
            'warn_id', 'user_id', 'server_id', 'reason', 'timestamp'
        ])
        df_warns.to_csv(WARNS_CSV, index=False)
        print("[ DATABASE ] warns.csv created.")

    # Tickets Table
    if not os.path.exists(TICKETS_CSV):
        df_tickets = pd.DataFrame(columns=[
            'ticket_id', 'user_id', 'server_id', 'status', 'created_at'
        ])
        df_tickets.to_csv(TICKETS_CSV, index=False)
        print("[ DATABASE ] tickets.csv created.")

    print("[ DATABASE ] All CSV databases are ready.")

# Utility functions to read/write to CSV
def get_user(user_id):
    df = pd.read_csv(USERS_CSV)
    user = df[df['user_id'] == str(user_id)]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

def save_user(user_data):
    df = pd.read_csv(USERS_CSV)
    user_id_str = str(user_data['user_id'])
    
    if user_id_str in df['user_id'].astype(str).values:
        for key, value in user_data.items():
            df.loc[df['user_id'].astype(str) == user_id_str, key] = value
    else:
        new_row = pd.DataFrame([user_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
    df.to_csv(USERS_CSV, index=False)

if __name__ == "__main__":
    init_db()
