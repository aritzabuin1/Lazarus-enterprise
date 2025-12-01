from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from app.domain.models import LeadCreate, Lead

class LeadRepository(ABC):
    @abstractmethod
    def create_lead(self, lead: LeadCreate) -> Lead:
        pass

    @abstractmethod
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        pass

class ConversationRepository(ABC):
    @abstractmethod
    def save_message(self, lead_id: str, role: str, content: str) -> None:
        pass

class LLMProvider(ABC):
    @abstractmethod
    def analyze_intent(self, messages: List[BaseMessage]) -> str:
        pass

    @abstractmethod
    def generate_reply(self, messages: List[BaseMessage], context: Dict[str, Any], intent: str) -> BaseMessage:
        pass
