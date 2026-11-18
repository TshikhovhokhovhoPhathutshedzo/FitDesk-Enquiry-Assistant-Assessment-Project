from . import deepseek_client, gemini_client, groq_client, openrouter_client
from .config import AI_PROVIDER
from .gemini_client import AIServiceError
from .models import EnquiryAnalysis

_PROVIDERS = {
    "gemini": gemini_client,
    "deepseek": deepseek_client,
    "openrouter": openrouter_client,
    "groq": groq_client,
}


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    """Route the enquiry to the provider selected in .env."""
    try:
        provider = _PROVIDERS[AI_PROVIDER]
    except KeyError as exc:
        choices = ", ".join(_PROVIDERS)
        raise AIServiceError(
            f"Unsupported AI_PROVIDER {AI_PROVIDER!r}. Choose {choices}."
        ) from exc
    return provider.analyze_enquiry(message)
