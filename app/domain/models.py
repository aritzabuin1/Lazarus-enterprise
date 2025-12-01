from enum import Enum
from typing import Optional, Dict, Any, List, TypedDict, Literal, Annotated
from pydantic import BaseModel, EmailStr, Field, field_validator
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import phonenumbers

# --- Enums ---
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    BOOKED = "booked"
    LOST = "lost"

# --- Entities ---
class LeadBase(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: LeadStatus = LeadStatus.NEW
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            parsed_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError('Invalid phone number format')
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format')

class LeadCreate(LeadBase):
    campaign_id: str

class Lead(LeadBase):
    id: str
    campaign_id: str
    created_at: str

    class Config:
        from_attributes = True

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    lead_context: Dict[str, Any]
    intent: Literal["buy", "doubt", "unknown"]
