from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langfuse.callback import CallbackHandler
from app.domain.ports import LLMProvider
from app.logger import logger
from app.core.config import settings
from app.core.ai_security import ai_security

# Try importing GPTCache
try:
    from gptcache import cache
    from gptcache.adapter.api import init_similar_cache
    from gptcache.processor.pre import get_prompt
    GPTCACHE_AVAILABLE = True
except ImportError:
    GPTCACHE_AVAILABLE = False

class OpenAIAdapter(LLMProvider):
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.client = ChatOpenAI(model=model_name, temperature=temperature)
        
        # Initialize LangFuse Callback
        self.langfuse_handler: Optional[CallbackHandler] = None
        if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
            self.langfuse_handler = CallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST
            )
            
        # Initialize Semantic Cache (Mock/Simple for now)
        if GPTCACHE_AVAILABLE:
            try:
                # In production, use Redis. Here using Map (Memory) for demo.
                init_similar_cache(cache_strategy="distance")
                logger.info("✅ GPTCache initialized (Semantic Caching Enabled).")
            except Exception as e:
                logger.warning(f"⚠️ GPTCache init failed: {e}")

    def _get_callbacks(self):
        return [self.langfuse_handler] if self.langfuse_handler else []

    def analyze_intent(self, messages: List[BaseMessage]) -> str:
        # 1. Redact PII from input (Security)
        # We only redact the last user message to avoid breaking context structure too much
        if messages and isinstance(messages[-1], HumanMessage):
            original_content = messages[-1].content
            redacted_content = ai_security.redact_pii(original_content)
            if original_content != redacted_content:
                logger.info("🛡️ PII Detected and Redacted in Intent Analysis")
                messages[-1].content = redacted_content

        last_message = messages[-1].content if messages else ""
        logger.info(f"Analyzing intent for: {last_message}")
        
        classifier = ChatOpenAI(model=self.model_name, temperature=0)
        
        system_prompt = """
        You are an intent classifier. Classify the user's message into one of these categories:
        - 'buy': User wants to purchase, book, or sign up.
        - 'doubt': User has a question, objection, or needs more info.
        - 'unknown': Anything else.
        
        Return ONLY the category name.
        """
        
        response = classifier.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ],
            config={"callbacks": self._get_callbacks()}
        )
        
        intent = response.content.strip().lower()
        if intent not in ["buy", "doubt", "unknown"]:
            intent = "unknown"
            
        return intent

    def generate_reply(self, messages: List[BaseMessage], context: Dict[str, Any], intent: str) -> BaseMessage:
        # 1. Redact PII (Security)
        if messages and isinstance(messages[-1], HumanMessage):
            messages[-1].content = ai_security.redact_pii(messages[-1].content)

        logger.info(f"Generating reply for intent: {intent}")
        
        system_prompt = f"""
        You are a helpful sales assistant.
        Context about the lead: {context}
        
        Current intent: {intent}
        
        If intent is 'buy', encourage them to book a call or finalize.
        If intent is 'doubt', answer their question and reassure them.
        If intent is 'unknown', ask for clarification.
        """
        
        full_messages = [SystemMessage(content=system_prompt)] + messages
        
        # 2. Check Semantic Cache (Optimization)
        # Note: Proper integration with LangChain requires wrapping the LLM or manual check.
        # For simplicity in this adapter, we proceed with direct call but note the place for cache.
        
        response = self.client.invoke(
            full_messages,
            config={"callbacks": self._get_callbacks()}
        )
        
        # 3. Validate Output (Guardrails)
        if not ai_security.validate_output(response.content):
            logger.warning("🛡️ Guardrails blocked unsafe response.")
            response.content = "I apologize, but I cannot provide that answer."
            
        return response
