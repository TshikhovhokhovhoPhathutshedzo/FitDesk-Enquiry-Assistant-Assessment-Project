from . import gemini_client
from .config import GEMINI_MODEL
from .models import EnquiryAnalysis


def get_provider_metadata() -> dict:
    """Return the Gemini model name for the status log; never include its key."""
    return {
        "ai_provider": "gemini",
        "ai_model": GEMINI_MODEL,
    }


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    """Classify an enquiry using Gemini."""
    return gemini_client.analyze_enquiry(message)
