import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Document extraction: try primary, then each fallback in order
DOCUMENT_MODEL = os.getenv("DOCUMENT_MODEL", "gemini-3.5-flash-lite")
_DEFAULT_DOCUMENT_FALLBACKS = (
    "gemini-3.1-flash-lite,"
    "gemini-3.5-flash,"
    "gemini-3.6-flash,"
    "gemini-3.7-flash,"
    "gemini-3.8-flash,"
    "gemini-3-flash-preview,"
    "gemini-2.5-flash-lite,"
    "gemini-2.5-flash"
)
DOCUMENT_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("DOCUMENT_FALLBACK_MODELS", _DEFAULT_DOCUMENT_FALLBACKS).split(",")
    if m.strip()
]

# Verified active Groq fallback models
_DEFAULT_FALLBACKS = (
    "qwen/qwen3.8-27b,"
    "qwen/qwen3.6-27b,"
    "openai/gpt-oss-20b,"
    "groq/compound,"
    "groq/compound-mini"
)
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("FALLBACK_MODELS", _DEFAULT_FALLBACKS).split(",")
    if m.strip()
]

