from typing import List, Optional, Dict, Any 
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from app.domain.models import LeadCreate, Lead, User
from app.database import supabase
from app.logger import logger
from app.adapters.supabase_repo import SupabaseAdapter
from app.adapters.openai_llm import OpenAIAdapter
from app.agent_logic import create_agent_graph
from app.tasks.chat_tasks import process_chat
from app.api.routers import campaign, auth
from app.core.config import settings
from app.core.errors import global_exception_handler, AppError
from app.core.security import create_access_token
import sentry_sdk

# --- Sentry Initialization ---
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# --- Rate Limiting Setup ---
# Using Redis if available, else memory (fallback)
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

app = FastAPI(title="Lazarus Enterprise API")

# --- Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "your-production-domain.com"]
)

# --- Routers ---
app.include_router(auth.router)
app.include_router(campaign.router)

# --- Dependency Injection ---
supabase_adapter = SupabaseAdapter(supabase)
openai_adapter = OpenAIAdapter()
agent_app = create_agent_graph(llm=openai_adapter, repo=supabase_adapter)

# --- Health Check ---
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# --- Protected Endpoints ---
@app.post("/leads", response_model=List[Lead], status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
async def create_leads(
    request: Request, 
    leads: List[LeadCreate], 
    current_user: User = Depends(auth.get_current_user)
):
    logger.info(f"Received request to create {len(leads)} leads by {current_user.email}")
    
    if not leads:
        return []

    created_leads = []
    try:
        for lead in leads:
            created_lead = supabase_adapter.create_lead(lead)
            created_leads.append(created_lead)
            
        logger.info(f"Successfully created {len(created_leads)} leads")
        return created_leads

    except Exception as e:
        logger.error(f"Error creating leads: {str(e)}")
        raise AppError(f"Error creating leads: {str(e)}", status_code=500)

class ChatRequest(BaseModel):
    message: str
    lead_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None

@app.post("/chat", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("50/minute")
async def chat_endpoint(
    request: Request, 
    chat_req: ChatRequest,
    current_user: User = Depends(auth.get_current_user)
):
    """
    Async chat endpoint. Queues the message for processing by the AI agent.
    """
    logger.info(f"Received chat request for lead {chat_req.lead_id} from {current_user.email}")
    
    context = {"id": chat_req.lead_id}
    task = process_chat.delay(chat_req.message, context)
    
    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Message queued for processing"
    }

from celery.result import AsyncResult

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(auth.get_current_user)):
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
