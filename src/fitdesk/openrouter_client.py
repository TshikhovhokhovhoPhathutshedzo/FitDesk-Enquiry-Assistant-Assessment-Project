"""OpenRouter settings for the shared OpenAI-compatible chat-completion client."""

from .chat_completion import analyze_chat_completion
from .config import OPENROUTER_API_KEY, OPENROUTER_MODEL, REQUEST_TIMEOUT_SECONDS
from .models import EnquiryAnalysis

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    return analyze_chat_completion(
        provider="OpenRouter",
        endpoint=OPENROUTER_CHAT_COMPLETIONS_URL,
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
        message=message,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
