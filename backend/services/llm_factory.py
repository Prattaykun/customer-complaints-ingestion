"""
LLM Factory with Multi-Model Fallback for GroqCloud.
Dynamically filters models based on tool-calling capabilities and availability.
"""

from typing import List, Optional
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME, FALLBACK_MODELS

# Models verified to support OpenAI-style tool calling on Groq API
TOOL_CAPABLE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b",
]

# General text generation models for non-tool tasks
GENERAL_MODELS = [
    "groq/compound",
    "groq/compound-mini",
    "allam-2-7b",
]


def get_groq_llm(
    temperature: float = 0.1,
    max_tokens: int = 2048,
    tools: Optional[list] = None,
    tool_choice: Optional[str] = None,
):
    """
    Construct a ChatGroq LLM instance with fallback models.
    Primary model is MODEL_NAME. If it encounters errors or rate limits,
    it automatically falls back through the FALLBACK_MODELS sequence.
    """
    is_tool_mode = bool(tools)

    # Filter allowed model IDs based on tool capability
    allowed_list = TOOL_CAPABLE_MODELS if is_tool_mode else (TOOL_CAPABLE_MODELS + GENERAL_MODELS)
    allowed_set = set(allowed_list)

    all_models: List[str] = []

    # Ensure primary model is first if allowed
    if MODEL_NAME and MODEL_NAME.strip() in allowed_set:
        all_models.append(MODEL_NAME.strip())

    # Add configured fallback models if allowed
    for model in FALLBACK_MODELS:
        m = model.strip()
        if m in allowed_set and m not in all_models:
            all_models.append(m)

    # Ensure all default allowed candidates are appended as backup
    for m in allowed_list:
        if m not in all_models:
            all_models.append(m)

    instances = []
    for model_id in all_models:
        chat = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            if tool_choice:
                chat = chat.bind_tools(tools, tool_choice=tool_choice)
            else:
                chat = chat.bind_tools(tools)
        instances.append(chat)

    primary_llm = instances[0]
    fallback_llms = instances[1:]

    if fallback_llms:
        return primary_llm.with_fallbacks(fallback_llms)
    return primary_llm
