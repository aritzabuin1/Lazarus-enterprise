from typing import Optional, List
from supabase import Client
from app.domain.ports import LeadRepository, ConversationRepository
from app.domain.models import Lead, LeadCreate
from app.logger import logger

class SupabaseAdapter(LeadRepository, ConversationRepository):
    def __init__(self, client: Client):
        self.client = client

    def create_lead(self, lead: LeadCreate) -> Lead:
        logger.info(f"Creating lead: {lead.phone}")
        data = lead.model_dump(mode='json')
        response = self.client.table("leads").insert(data).execute()
        if not response.data:
            raise Exception("Failed to create lead")
        return Lead(**response.data[0])

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        response = self.client.table("leads").select("*").eq("id", lead_id).execute()
        if not response.data:
            return None
        return Lead(**response.data[0])

    def save_message(self, lead_id: str, role: str, content: str) -> None:
        logger.info(f"Saving message for lead {lead_id}")
        try:
            self.client.table("conversations").insert({
                "lead_id": lead_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            # We might want to re-raise or handle differently depending on requirements
