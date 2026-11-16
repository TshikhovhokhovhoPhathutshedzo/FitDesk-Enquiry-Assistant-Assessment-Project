from . import deepseek_client, gemini_client, openrouter_client
from .config import AI_PROVIDER
from .gemini_client import AIServiceError
from .models import EnquiryAnalysis


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    if AI_PROVIDER == "gemini":
        return gemini_client.analyze_enquiry(message)
    if AI_PROVIDER == "deepseek":
        return deepseek_client.analyze_enquiry(message)
    if AI_PROVIDER == "openrouter":
        return openrouter_client.analyze_enquiry(message)
    raise AIServiceError(
        f"Unsupported AI_PROVIDER {AI_PROVIDER!r}. "
        "Choose 'gemini', 'deepseek', or 'openrouter'."
    )
