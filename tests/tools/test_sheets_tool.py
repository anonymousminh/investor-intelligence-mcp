import pytest
from unittest.mock import patch, MagicMock, mock_open
from investor_intelligence.tools import sheets_tool
import os


# Mock the build function from googleapiclient.discovery
@patch("builtins.open", new_callable=mock_open)
@patch("investor_intelligence.tools.sheets_tool.build")
# Mock the InstalledAppFlow from google_auth_oauthlib.flow
@patch("investor_intelligence.tools.sheets_tool.InstalledAppFlow")
# Mock os.path.exists to control token.pickle presence
@patch("investor_intelligence.tools.sheets_tool.os.path.exists")
# Mock pickle.load and pickle.dump
@patch("investor_intelligence.tools.sheets_tool.pickle")
def test_get_sheets_service_new_auth(
    mock_pickle, mock_exists, mock_flow, mock_build, mock_file
):
    mock_exists.side_effect = (
        lambda path: print(f"os.path.exists called with: {path}") or False
    )
    mock_pickle.load.side_effect = Exception("No valid creds")
    mock_creds = MagicMock()
    mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = (
        mock_creds
    )

    # Compute the expected credentials path as in the implementation
    sheets_tool_file = os.path.abspath(sheets_tool.__file__)
    base_dir = os.path.dirname(os.path.dirname(sheets_tool_file))
    credentials_path = os.path.join(base_dir, "..", "..", "config", "credentials.json")
    credentials_path = os.path.abspath(credentials_path)

    # Print the expected and actual arguments for debugging
    print("Expected credentials_path:", credentials_path)
    print("Actual call args:", mock_flow.from_client_secrets_file.call_args)

    service = sheets_tool.get_sheets_service()

    mock_flow.from_client_secrets_file.assert_called_once_with(
        credentials_path,
        ["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    mock_build.assert_called_once_with("sheets", "v4", credentials=mock_creds)
    mock_pickle.dump.assert_called_once_with(mock_creds, mock_file.return_value)
    assert service is not None


@patch("investor_intelligence.tools.sheets_tool.get_sheets_service")
def test_read_spreadsheet_data(mock_get_sheets_service):
    mock_service = MagicMock()
    mock_get_sheets_service.return_value = mock_service

    # Configure the mock service to return sample data
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [["Header1", "Header2"], ["Data1", "Data2"]]
    }

    spreadsheet_id = "test_id"
    range_name = "Sheet1!A1:B2"

    data = sheets_tool.read_spreadsheet_data(spreadsheet_id, range_name)

    mock_service.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
        spreadsheetId=spreadsheet_id, range=range_name
    )
    assert data == [["Header1", "Header2"], ["Data1", "Data2"]]


@patch("investor_intelligence.tools.sheets_tool.get_sheets_service")
def test_read_spreadsheet_data_no_values(mock_get_sheets_service):
    mock_service = MagicMock()
    mock_get_sheets_service.return_value = mock_service

    # Configure the mock service to return no values
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = (
        {}
    )

    data = sheets_tool.read_spreadsheet_data(
        "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q", "Sheet1!A1:B2"
    )

    assert data == []
