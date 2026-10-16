"""
agent/llm.py — Factory for initializing the configured LLM instance.
Supports Google Gemini and OpenAI with automatic retries and fallback.
"""
from agent.config import LLM_PROVIDER, LLM_MODEL, GOOGLE_KEY, OPENAI_KEY, logger


def get_llm():
    """
    Returns an initialized Chat model based on LLM_PROVIDER.
    Defaults to ChatGoogleGenerativeAI (gemini-3.8-flash).
    """
    if LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.debug(f"Initializing Gemini model: {LLM_MODEL}")
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_KEY,
            temperature=0.2,
            max_retries=0,
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        logger.debug(f"Initializing OpenAI model: {LLM_MODEL}")
        return ChatOpenAI(
            model=LLM_MODEL,
            api_key=OPENAI_KEY,
            temperature=0.2,
            max_retries=3,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
