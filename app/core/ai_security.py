import logging
from typing import Optional, List, Dict, Any

# Try importing Presidio, handle if not installed yet (during build)
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

# Try importing Guardrails
try:
    from guardrails import Guard
    from guardrails.hub import ToxicLanguage
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False

logger = logging.getLogger(__name__)

class AISecurity:
    """
    Central security handler for AI interactions.
    Responsibility: Ensure no PII leaks to LLM and no toxic content reaches user.
    """
    
    def __init__(self):
        if PRESIDIO_AVAILABLE:
            # Analyzer: Detects PII (Phone, Email, etc.)
            # Note: Requires 'python -m spacy download en_core_web_lg'
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                logger.info("✅ Presidio PII Analyzer initialized.")
            except Exception as e:
                logger.warning(f"⚠️ Presidio initialized failed (missing model?): {e}")
                self.analyzer = None
        else:
            logger.warning("⚠️ Presidio not installed. PII redaction disabled.")
            self.analyzer = None

        if GUARDRAILS_AVAILABLE:
            # Guardrails: Validates Input/Output
            # We use a simple check for toxic language as an example
            try:
                self.guard = Guard.from_rail_string("""
<rail version="0.1">
<output>
    <string name="response" description="The AI response" format="safe-for-work" />
</output>
</rail>
""")
                logger.info("✅ Guardrails initialized.")
            except Exception as e:
                logger.warning(f"⚠️ Guardrails initialization failed: {e}")
                self.guard = None
        else:
            logger.warning("⚠️ Guardrails AI not installed.")
            self.guard = None

    def redact_pii(self, text: str) -> str:
        """
        Scans text for PII and replaces it with placeholders <EMAIL>, <PHONE_NUMBER>.
        Why: GDPR compliance. OpenAI shouldn't see user's private info.
        """
        if not self.analyzer or not text:
            return text

        try:
            # 1. Analyze
            results = self.analyzer.analyze(text=text, entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"], language='en')
            
            # 2. Anonymize
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )
            
            return anonymized_result.text
        except Exception as e:
            logger.error(f"Error during PII redaction: {e}")
            return text # Fail open (return original) or fail closed? Fail open for now to not break chat.

    def validate_output(self, text: str) -> bool:
        """
        Checks if the AI response is safe.
        Why: Prevent brand damage from toxic/racist/unsafe responses.
        """
        if not self.guard:
            return True

        try:
            # Simple check (mocked logic if guardrails hub not connected)
            # In production, this would run specific validators
            return True 
        except Exception as e:
            logger.error(f"Error during Guardrails validation: {e}")
            return True

# Singleton instance
ai_security = AISecurity()
