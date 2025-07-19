import os
import pickle
from email.mime.text import MIMEText
import base64

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def get_gmail_service():
    """Shows basic usage of the Gmail API."""
    creds = None
    # Find the absolute path to config/credentials.json relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(base_dir, "..", "..", "config", "credentials.json")
    credentials_path = os.path.abspath(credentials_path)
    fallback_path = os.path.join(
        base_dir,
        "..",
        "..",
        "config",
        "credentials.json",
    )
    fallback_path = os.path.abspath(fallback_path)
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
            else:
                flow = InstalledAppFlow.from_client_secrets_file(fallback_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)
    return service


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: Subject of the email.
        message_text: Text of the email.

    Returns:
        An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me" can be used to indicate the authenticated user.
        message: Message to be sent.

    Returns:
        Sent Message.
    """
    try:
        message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print(f"Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


if __name__ == "__main__":
    # Example usage:
    service = get_gmail_service()
    sender_email = "me"  # "me" refers to the authenticated user
    recipient_email = "cookieoil7999@gmail.com"  # Replace with a test recipient email
    email_subject = "Test Email from Investor Intelligence Agent"
    email_body = "This is a test email sent from the Investor Intelligence Agent MCP Server. If you received this, the Gmail integration is working!"

    message = create_message(sender_email, recipient_email, email_subject, email_body)
    send_message(service, sender_email, message)
