"""Groq settings for the shared OpenAI-compatible chat-completion client."""

from .chat_completion import analyze_chat_completion
from .config import GROQ_API_KEY, GROQ_MODEL, REQUEST_TIMEOUT_SECONDS
from .models import EnquiryAnalysis

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    return analyze_chat_completion(
        provider="Groq",
        endpoint=GROQ_CHAT_COMPLETIONS_URL,
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        message=message,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
