"""Configuration: which LLM provider/model to use, read from environment (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Every provider below speaks the OpenAI "chat completions + tools" format,
# so one client works for all of them. Only the URL and model name change.
PROVIDERS = {
    "groq":   {"base_url": "https://api.groq.com/openai/v1",
               "model": "openai/gpt-oss-120b"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "model": "gemini-2.5-flash"},
    "ollama": {"base_url": "http://localhost:11434/v1",
               "model": "qwen2.5-coder:7b"},
    "openai": {"base_url": None,
               "model": "gpt-4o-mini"},
}


@dataclass
class Config:
    provider: str
    api_key: str
    model: str
    base_url: str | None
    max_steps: int = 25


def load_config() -> Config:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider not in PROVIDERS:
        raise SystemExit(f"Unknown LLM_PROVIDER '{provider}'. Choose from: {', '.join(PROVIDERS)}")
    preset = PROVIDERS[provider]
    api_key = os.getenv("LLM_API_KEY", "ollama" if provider == "ollama" else "")
    if not api_key:
        raise SystemExit("LLM_API_KEY is missing. Copy .env.example to .env and add your key.")
    return Config(
        provider=provider,
        api_key=api_key,
        model=os.getenv("LLM_MODEL") or preset["model"],
        base_url=preset["base_url"],
        max_steps=int(os.getenv("MAX_STEPS", "25")),
    )
