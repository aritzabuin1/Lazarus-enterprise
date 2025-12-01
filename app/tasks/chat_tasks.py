from typing import Dict, Any
import requests
from langchain_core.messages import HumanMessage
from app.core.celery_app import celery_app
from app.core.config import settings
from app.logger import logger
from app.agent_logic import create_agent_graph
from app.adapters.supabase_repo import SupabaseAdapter
from app.adapters.openai_llm import OpenAIAdapter
from app.database import supabase

# Instantiate dependencies and agent at module level
# This ensures they are created once per worker process
try:
    supabase_adapter = SupabaseAdapter(supabase)
    openai_adapter = OpenAIAdapter()
    agent_app = create_agent_graph(llm=openai_adapter, repo=supabase_adapter)
except Exception as e:
    logger.error(f"Failed to initialize agent in worker: {e}")
    agent_app = None

@celery_app.task(name='process_chat')
def process_chat(message: str, lead_context: Dict[str, Any]):
    """
    Process a chat message using the AI agent.
    """
    logger.info(f"Worker received message for lead {lead_context.get('id')}: {message}")

    if not agent_app:
        logger.error("Agent app is not initialized. Cannot process message.")
        return "Internal Error: Agent not initialized"

    try:
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "lead_context": lead_context,
            "intent": "unknown"
        }

        # Invoke the agent
        final_state = agent_app.invoke(initial_state)
        
        # Extract the response
        messages = final_state.get("messages", [])
        if messages:
            last_message = messages[-1]
            response_content = last_message.content
            logger.info(f"Agent generated response: {response_content[:50]}...")
            
            # Notify n8n
            try:
                if settings.N8N_WEBHOOK_URL:
                    payload = {
                        "lead_id": lead_context.get("id"),
                        "phone": lead_context.get("phone"),
                        "response": response_content
                    }
                    requests.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=10)
                    logger.info("🔔 Notificación enviada a n8n")
                else:
                    logger.info("N8N_WEBHOOK_URL not set, skipping notification")
            except Exception as e:
                logger.warning(f"⚠️ Fallo al notificar a n8n (pero la tarea IA terminó bien): {e}")

            return response_content
        else:
            logger.warning("Agent returned no messages.")
            return None

    except Exception as e:
        logger.error(f"Error processing chat task: {str(e)}")
        # We might want to retry here using self.retry()
        return f"Error: {str(e)}"
