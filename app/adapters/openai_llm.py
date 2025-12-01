from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from app.domain.ports import LLMProvider
from app.logger import logger

class OpenAIAdapter(LLMProvider):
    def __init__(self, model_name: str = "gpt-5-mini", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        # We initialize the client here, or we could pass it in. 
        # For simplicity, we create it here as it depends on env vars handled by langchain.
        self.client = ChatOpenAI(model=model_name, temperature=temperature)

    def analyze_intent(self, messages: List[BaseMessage]) -> str:
        last_message = messages[-1].content if messages else ""
        logger.info(f"Analyzing intent for: {last_message}")
        
        # Use a specialized client or same one with low temp
        classifier = ChatOpenAI(model=self.model_name, temperature=0)
        
        system_prompt = """
        You are an intent classifier. Classify the user's message into one of these categories:
        - 'buy': User wants to purchase, book, or sign up.
        - 'doubt': User has a question, objection, or needs more info.
        - 'unknown': Anything else.
        
        Return ONLY the category name.
        """
        
        response = classifier.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_message)
        ])
        
        intent = response.content.strip().lower()
        if intent not in ["buy", "doubt", "unknown"]:
            intent = "unknown"
            
        return intent

    def generate_reply(self, messages: List[BaseMessage], context: Dict[str, Any], intent: str) -> BaseMessage:
        logger.info(f"Generating reply for intent: {intent}")
        
        system_prompt = f"""
        You are a helpful sales assistant.
        Context about the lead: {context}
        
        Current intent: {intent}
        
        If intent is 'buy', encourage them to book a call or finalize.
        If intent is 'doubt', answer their question and reassure them.
        If intent is 'unknown', ask for clarification.
        """
        
        response = self.client.invoke([SystemMessage(content=system_prompt)] + messages)
        return response
