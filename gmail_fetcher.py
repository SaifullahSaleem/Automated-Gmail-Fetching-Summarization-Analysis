# gmail_fetcher.py
import os
import base64
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, SCOPES

# The file token.json stores the user's access and refresh tokens
TOKEN_FILE = 'token.json'

class GmailFetcher:
    """Handles Google OAuth, token management, and email fetching/decoding."""

    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        """Authenticates with Google using the installed app flow."""
        creds = None
        
        # Load token if it exists
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
        # If token is expired or not present, run the flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # This opens the browser for the user to log in and grant permissions
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("✅ Google Authentication successful and token saved.")
        
        # Build the Gmail service client
        return build('gmail', 'v1', credentials=creds)

    def _get_message_body(self, payload) -> str:
        """Recursively decodes and extracts the plain text body from a Gmail message payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                # Prioritize 'text/plain' over 'text/html' for LLM processing
                if part['mimeType'] == 'text/plain':
                    return self._decode_data(part['body'].get('data'))
                # Recurse for nested parts (e.g., multipart/alternative)
                elif 'parts' in part:
                    body = self._get_message_body(part)
                    if body:
                        return body
        elif 'body' in payload and 'data' in payload['body']:
            # Handle messages that are not multipart
            return self._decode_data(payload['body'].get('data'))
        
        return "Body content could not be reliably extracted."

    def _decode_data(self, data: str) -> str:
        """Decodes base64url data used by the Gmail API."""
        if not data:
            return ""
        # The Gmail API uses base64url, which requires base64.urlsafe_b64decode
        decoded_bytes = base64.urlsafe_b64decode(data + '==') # Add padding for safety
        return decoded_bytes.decode('utf-8', errors='ignore')

    def get_emails_for_day(self, date_str: str) -> list[dict]:
        """Fetches all emails received on a specific date."""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        next_day = date_obj + timedelta(days=1)
        
        # Gmail API query uses after:YYYY/MM/DD before:YYYY/MM/DD+1
        search_query = (
            f"after:{date_obj.strftime('%Y/%m/%d')} "
            f"before:{next_day.strftime('%Y/%m/%d')}"
        )
        
        print(f"Searching Gmail with query: {search_query}")
        
        emails = []
        # Get a list of message IDs first (max 500 per call, we ignore pagination for simplicity)
        response = self.service.users().messages().list(userId='me', q=search_query).execute()
        messages = response.get('messages', [])

        if not messages:
            return []

        # Fetch full content for each message
        for msg_id_info in messages:
            msg = self.service.users().messages().get(userId='me', id=msg_id_info['id'], format='full').execute()
            
            payload = msg['payload']
            
            # Extract Headers (Subject, From)
            headers = {h['name']: h['value'] for h in payload['headers']}
            
            email_data = {
                'id': msg['id'],
                'subject': headers.get('Subject', 'No Subject'),
                'sender': headers.get('From', 'Unknown Sender'),
                'receivedDateTime': datetime.fromtimestamp(int(msg['internalDate']) / 1000).isoformat(),
                'body': self._get_message_body(payload)
            }
            emails.append(email_data)
        
        return emails

    @staticmethod
    def format_email_for_langchain(email: dict) -> str:
        """Helper to format a single email into a string for the LLM context."""
        return (
            f"Subject: {email.get('subject', 'No Subject')}\n"
            f"From: {email.get('sender', 'Unknown Sender')}\n"
            f"Date: {email.get('receivedDateTime')}\n"
            f"Body: {email.get('body', '')}\n"
            "---"
        )