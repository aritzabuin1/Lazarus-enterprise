from typing import TypedDict, List, Dict, Any, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langfuse import observe
from app.domain.ports import LLMProvider, ConversationRepository
from app.domain.models import AgentState
from app.logger import logger

# We wrap the graph creation in a factory to inject dependencies
def create_agent_graph(llm: LLMProvider, repo: ConversationRepository):
    
    @observe()
    def analyze_intent(state: AgentState) -> AgentState:
        messages = state["messages"]
        intent = llm.analyze_intent(messages)
        return {"intent": intent}

    @observe()
    def generate_reply(state: AgentState) -> AgentState:
        intent = state.get("intent", "unknown")
        lead_context = state.get("lead_context", {})
        messages = state["messages"]
        
        response = llm.generate_reply(messages, lead_context, intent)
        return {"messages": [response]}

    @observe()
    def save_memory(state: AgentState) -> AgentState:
        messages = state["messages"]
        lead_context = state.get("lead_context", {})
        lead_id = lead_context.get("id")
        
        if not lead_id:
            logger.warning("No lead_id found in context, skipping save.")
            return {}

        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage):
            role = "assistant"
        elif isinstance(last_message, HumanMessage):
            role = "user"
        else:
            role = "unknown"

        repo.save_message(lead_id, role, last_message.content)
        return {}

    # --- Graph Construction ---
    workflow = StateGraph(AgentState)

    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("generate_reply", generate_reply)
    workflow.add_node("save_memory", save_memory)

    workflow.set_entry_point("analyze_intent")

    workflow.add_edge("analyze_intent", "generate_reply")
    workflow.add_edge("generate_reply", "save_memory")
    workflow.add_edge("save_memory", END)

    return workflow.compile()
