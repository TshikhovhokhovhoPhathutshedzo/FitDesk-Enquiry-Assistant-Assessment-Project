import json

from google import genai

from .config import GEMINI_API_KEY, GEMINI_MODEL, REQUEST_TIMEOUT_SECONDS
from .models import EnquiryAnalysis


class AIServiceError(RuntimeError):
    pass


class InvalidJSONError(AIServiceError):
    pass


class SchemaValidationError(AIServiceError):
    pass


def analyze_enquiry(message: str) -> EnquiryAnalysis:
    if not GEMINI_API_KEY:
        raise AIServiceError("Gemini API key is missing. Add it to .env.")

    prompt = (
        "You are classifying a fitness studio enquiry. Return valid JSON only with keys: "
        "intent, details, packages, saturday_times, requires_human_approval. "
        "Allowed intent values are pricing, availability, pricing_and_availability, other. "
        "Use the exact package names or Saturday times from the file when available. "
        "Do not invent unavailable facts.\n\nCustomer message: "
        f"{message}"
    )

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.1,
                "timeout": REQUEST_TIMEOUT_SECONDS,
            },
        )
    except Exception as exc:  # pragma: no cover - real service branch
        raise AIServiceError(f"Gemini service failed: {exc}") from exc

    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise InvalidJSONError("Gemini returned an empty response.")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidJSONError(f"Gemini returned invalid JSON: {exc}") from exc

    try:
        return EnquiryAnalysis.model_validate(payload)
    except Exception as exc:  # pragma: no cover - structured-output validation path
        raise SchemaValidationError(f"Gemini payload failed validation: {exc}") from exc
