import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tasks.chat_tasks import process_chat

def test_n8n_notification():
    print("\n🧪 [Notification] Testing n8n Webhook...")
    
    message = "Hola, test notificación"
    lead_context = {"id": "lead-n8n", "phone": "+1234567890"}
    
    # Mock dependencies
    with patch("app.tasks.chat_tasks.agent_app") as mock_agent, \
         patch("app.tasks.chat_tasks.requests.post") as mock_post, \
         patch("app.tasks.chat_tasks.settings") as mock_settings:
        
        # Setup mocks
        mock_agent.invoke.return_value = {
            "messages": [MagicMock(content="Respuesta para n8n")]
        }
        
        # Case 1: URL is set
        mock_settings.N8N_WEBHOOK_URL = "http://fake-n8n.com/webhook"
        
        process_chat(message, lead_context)
        
        # Verify request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://fake-n8n.com/webhook"
        assert kwargs['json']['lead_id'] == "lead-n8n"
        assert kwargs['json']['response'] == "Respuesta para n8n"
        print("✅ Webhook triggered correctly when URL is set.")
        
        # Case 2: URL is not set
        mock_post.reset_mock()
        mock_settings.N8N_WEBHOOK_URL = ""
        
        process_chat(message, lead_context)
        
        mock_post.assert_not_called()
        print("✅ Webhook skipped correctly when URL is not set.")

if __name__ == "__main__":
    test_n8n_notification()
