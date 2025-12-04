from typing import List, Optional, Dict, Any 
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from app.domain.models import LeadCreate, Lead
from app.database import supabase
from app.logger import logger
from app.adapters.supabase_repo import SupabaseAdapter
from app.adapters.openai_llm import OpenAIAdapter
from app.agent_logic import create_agent_graph
from app.tasks.chat_tasks import process_chat
from app.api.routers import campaign

app = FastAPI(title="Lazarus Enterprise API")

app.include_router(campaign.router)

# --- Dependency Injection ---
# In a real app, use a DI container or Depends()
supabase_adapter = SupabaseAdapter(supabase)
openai_adapter = OpenAIAdapter()

# Create the agent graph with injected dependencies
agent_app = create_agent_graph(llm=openai_adapter, repo=supabase_adapter)

@app.post("/leads", response_model=List[Lead], status_code=status.HTTP_201_CREATED)
async def create_leads(leads: List[LeadCreate]):
    logger.info(f"Received request to create {len(leads)} leads")
    
    if not leads:
        return []

    created_leads = []
    try:
        # Use the adapter to create leads
        # Note: Our adapter creates one by one. For bulk, we might want to add a bulk method to the port.
        # For now, loop is fine for MVP.
        for lead in leads:
            created_lead = supabase_adapter.create_lead(lead)
            created_leads.append(created_lead)
            
        logger.info(f"Successfully created {len(created_leads)} leads")
        return created_leads

    except Exception as e:
        logger.error(f"Error creating leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

class ChatRequest(BaseModel):
    message: str
    lead_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None

@app.post("/chat", status_code=status.HTTP_202_ACCEPTED)
async def chat_endpoint(request: ChatRequest):
    """
    Async chat endpoint. Queues the message for processing by the AI agent.
    Returns a task ID for tracking.
    """
    logger.info(f"Received chat request for lead {request.lead_id}")
    
    # We pass the context as a dict. In a real app, we might fetch more context here.
    context = {"id": request.lead_id}
    
    # Offload to Celery worker
    task = process_chat.delay(request.message, context)
    
    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Message queued for processing"
    }

from celery.result import AsyncResult

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a background task.
    """
    task_result = AsyncResult(task_id)
    
    if task_result.ready():
        if task_result.successful():
             return {"status": "completed", "result": task_result.result}
        else:
             return {"status": "failed", "error": str(task_result.result)}
    else:
        return {"status": "processing"}
