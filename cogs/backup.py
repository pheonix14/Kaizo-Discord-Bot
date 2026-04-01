import disnake
from disnake.ext import commands, tasks
import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, 'database')

class DatabaseBackup(commands.Cog):
    """
    Handles automatic 24-hour backups of CSV databases to Google Drive.
    """
    def __init__(self, bot):
        self.bot = bot
        self.creds = None
        self.drive_service = None
        self.authenticate_google_drive()
        self.backup_task.start()

    def authenticate_google_drive(self):
        """
        Authenticates with Google Drive API.
        Requires credentials.json from Google Cloud Console.
        """
        token_path = os.path.join(DB_DIR, 'token.json')
        creds_path = os.path.join(DB_DIR, 'credentials.json')

        try:
            if os.path.exists(token_path):
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                elif os.path.exists(creds_path):
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())
                else:
                    print("[ WARNING ] credentials.json not found! Google Drive Backup disabled.")
                    return

            self.drive_service = build('drive', 'v3', credentials=self.creds)
            print("[ BACKUP ] Google Drive Authenticated Successfully.")
        except Exception as e:
            print(f"[ ERROR ] Google Drive Auth Failed: {e}")

    def upload_to_drive(self, filepath, filename):
        """
        Uploads a single file to Google Drive.
        """
        if not self.drive_service:
            return

        try:
            file_metadata = {'name': f"{datetime.datetime.now().strftime('%Y-%m-%d')}_{filename}"}
            media = MediaFileUpload(filepath, mimetype='text/csv')
            
            # Create a new file
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"[ BACKUP ] Uploaded {filename} to Drive with ID: {file.get('id')}")
        except Exception as e:
            print(f"[ ERROR ] Failed to upload {filename}: {e}")

    @tasks.loop(hours=24)
    async def backup_task(self):
        """
        Runs every 24 hours to upload CSV databases.
        """
        print("[ BACKUP ] Initiating 24-hour scheduled database backup to Google Drive...")
        files_to_backup = ['users.csv', 'servers.csv', 'warns.csv', 'tickets.csv']
        
        for file in files_to_backup:
            filepath = os.path.join(DB_PATH, file)
            if os.path.exists(filepath):
                # Run the blocking upload function in a thread to not block the bot
                self.bot.loop.run_in_executor(None, self.upload_to_drive, filepath, file)
            else:
                print(f"[ WARNING ] Backup skipped for {file} - File not found.")

    @backup_task.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(DatabaseBackup(bot))
