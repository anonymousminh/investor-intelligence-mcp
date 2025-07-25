import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_sheets_service():
    """
    Authenticate and return a Google Sheets API service client.

    Handles OAuth2 flow, token storage, and refresh. If no valid token is found, prompts the user to authenticate.

    Returns:
        googleapiclient.discovery.Resource: Authorized Sheets API service instance.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    print("Checking if token.pickle exists in:", os.path.abspath("token.pickle"))
    if os.path.exists("token.pickle"):
        print("token.pickle exists, attempting to load credentials...")
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired, refreshing...")
            creds.refresh(Request())
        else:
            # Find the absolute path to config/credentials.json relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(
                base_dir, "..", "..", "config", "credentials.json"
            )
            credentials_path = os.path.abspath(credentials_path)
            print(
                "About to call InstalledAppFlow.from_client_secrets_file with:",
                credentials_path,
            )
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)
    return service


def read_spreadsheet_data(spreadsheet_id, range_name):
    """
    Read data from a specified range in a Google Sheet.

    Args:
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        range_name (str): The A1 notation of the range to retrieve (e.g., 'Sheet1!A1:D10').

    Returns:
        list: List of rows (each row is a list of cell values). Returns an empty list if no data is found.
    """
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    )
    values = result.get("values", [])

    if not values:
        print("No data found.")
        return []
    else:
        return values


if __name__ == "__main__":
    # Example usage (replace with your spreadsheet ID and range)
    SAMPLE_SPREADSHEET_ID = "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"
    SAMPLE_RANGE_NAME = "Sheet1!A1:D"
    data = read_spreadsheet_data(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
    for row in data:
        print(row)
