"""DeepSeek settings for the shared OpenAI-compatible chat-completion client."""

from .chat_completion import analyze_chat_completion
from .config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, REQUEST_TIMEOUT_SECONDS
from .models import EnquiryAnalysis

DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    return analyze_chat_completion(
        provider="DeepSeek",
        endpoint=DEEPSEEK_CHAT_COMPLETIONS_URL,
        api_key=DEEPSEEK_API_KEY,
        model=DEEPSEEK_MODEL,
        message=message,
        timeout=REQUEST_TIMEOUT_SECONDS,
        extra_parameters={"thinking": {"type": "disabled"}},
    )
