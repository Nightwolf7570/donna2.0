"""Tests for Google authentication module."""

from unittest.mock import Mock, patch
from src.receptionist.google_auth import authenticate_google, SCOPES

@patch('src.receptionist.google_auth.Credentials')
@patch('src.receptionist.google_auth.os.path.exists')
def test_authenticate_google_existing_token(mock_exists, mock_creds):
    """Test authentication with existing valid token."""
    mock_exists.return_value = True
    mock_token = Mock()
    mock_token.valid = True
    mock_creds.from_authorized_user_file.return_value = mock_token
    
    auth = authenticate_google()
    
    assert auth == mock_token
    mock_creds.from_authorized_user_file.assert_called_with("token.json", SCOPES)

@patch('src.receptionist.google_auth.InstalledAppFlow')
@patch('src.receptionist.google_auth.os.path.exists')
def test_authenticate_google_new_auth(mock_exists, mock_flow):
    """Test authentication flow for new credentials."""
    # Simulate token file missing but credentials file present
    def exists_side_effect(path):
        return path == "credentials.json"
    mock_exists.side_effect = exists_side_effect
    
    mock_flow_instance = Mock()
    mock_flow.from_client_secrets_file.return_value = mock_flow_instance
    mock_creds = Mock()
    mock_flow_instance.run_local_server.return_value = mock_creds
    
    with patch('builtins.open', new_callable=Mock) as mock_open:
        auth = authenticate_google()
        
        assert auth == mock_creds
        mock_flow.from_client_secrets_file.assert_called_with("credentials.json", SCOPES)
        mock_flow_instance.run_local_server.assert_called()
