from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_create_leads_success():
    """
    Test creating a lead with valid data.
    Should return 201 Created and the created lead data.
    """
    # Mock response from Supabase
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": "test-uuid-123",
            "campaign_id": "campaign-uuid-456",
            "phone": "+14155552671",
            "name": "Alice Smith",
            "email": "alice@example.com",
            "status": "new",
            "metadata": {},
            "created_at": "2023-11-29T12:00:00Z"
        }
    ]
    
    # Patch the supabase client where it is used in app.main
    with patch("app.main.supabase") as mock_supabase:
        # Configure the mock chain: supabase.table().insert().execute()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        payload = [
            {
                "phone": "+14155552671",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "campaign_id": "campaign-uuid-456"
            }
        ]
        
        response = client.post("/leads", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["phone"] == "+14155552671"
        assert data[0]["id"] == "test-uuid-123"

def test_create_leads_missing_phone():
    """
    Test creating a lead without the required 'phone' field.
    Should return 422 Unprocessable Entity.
    """
    payload = [
        {
            "name": "Bob Jones",
            "campaign_id": "campaign-uuid-456"
            # Missing phone
        }
    ]
    
    response = client.post("/leads", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    # Verify that the error is about the missing field
    assert data["detail"][0]["loc"] == ["body", 0, "phone"]
    assert data["detail"][0]["msg"] == "Field required"
