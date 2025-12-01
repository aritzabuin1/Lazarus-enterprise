import sys
import os
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from app.domain.ports import LLMProvider, ConversationRepository, LeadRepository
from app.domain.models import Lead, LeadCreate
from app.agent_logic import create_agent_graph

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MOCKS ---
class MockLLM(LLMProvider):
    def __init__(self):
        self.responses = {
            "Hola": ("unknown", "Hola, ¿en qué puedo ayudarte?"),
            "Es muy caro": ("doubt", "Entiendo, pero vale la pena."),
            "Vale, lo compro": ("buy", "¡Genial! Vamos a procesarlo.")
        }

    def analyze_intent(self, messages: List[BaseMessage]) -> str:
        last_msg = messages[-1].content
        # Simple lookup for simulation
        return self.responses.get(last_msg, ("unknown", ""))[0]

    def generate_reply(self, messages: List[BaseMessage], context: Dict[str, Any], intent: str) -> BaseMessage:
        last_msg = messages[-1].content
        reply_text = self.responses.get(last_msg, ("", "Lo siento, no entiendo."))[1]
        return AIMessage(content=reply_text)

class MockRepo(ConversationRepository, LeadRepository):
    def __init__(self):
        self.messages = []
        self.leads = {}

    def save_message(self, lead_id: str, role: str, content: str) -> None:
        print(f"[MOCK DB] Saving message for {lead_id}: {role} -> {content}")
        self.messages.append({"lead_id": lead_id, "role": role, "content": content})

    def create_lead(self, lead: LeadCreate) -> Lead:
        lead_id = f"mock-lead-{len(self.leads) + 1}"
        new_lead = Lead(id=lead_id, created_at="2023-01-01", **lead.model_dump())
        self.leads[lead_id] = new_lead
        return new_lead

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        return self.leads.get(lead_id)

def run_simulation():
    print("Starting Clean Architecture Agent Simulation...")
    
    # 1. Instantiate Mocks
    mock_llm = MockLLM()
    mock_repo = MockRepo()
    
    # 2. Create Agent with Mocks
    agent_app = create_agent_graph(llm=mock_llm, repo=mock_repo)
    
    lead_context = {"id": "test-lead-123", "name": "Test User"}
    messages_to_send = [
        "Hola",
        "Es muy caro",
        "Vale, lo compro"
    ]
    
    for i, msg_content in enumerate(messages_to_send):
        print(f"\n--- Turn {i+1}: User says '{msg_content}' ---")
        
        initial_state = {
            "messages": [HumanMessage(content=msg_content)],
            "lead_context": lead_context,
            "intent": "unknown"
        }
        
        final_state = agent_app.invoke(initial_state)
        
        intent = final_state.get("intent")
        reply = final_state["messages"][-1].content
        
        print(f"Detected Intent: {intent}")
        print(f"Agent Reply: {reply}")

if __name__ == "__main__":
    run_simulation()
