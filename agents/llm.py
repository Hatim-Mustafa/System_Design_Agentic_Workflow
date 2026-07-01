from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"
DEFAULT_MODEL_NAME = "gpt-4o"

load_dotenv()


@lru_cache(maxsize=8)
def get_chat_model(model_name: str = DEFAULT_MODEL_NAME) -> ChatOpenAI:
    api_key = os.getenv("GITHUB_API_KEY")
    if not api_key:
        raise RuntimeError("GITHUB_API_KEY is not set. Add it to .env before running the agents.")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=GITHUB_MODELS_BASE_URL,
        temperature=0,
    )
