"""Configuration management for SafeSheet."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from project root (parent of safesheet directory)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration for SafeSheet."""

    @staticmethod
    def get_anthropic_api_key() -> Optional[str]:
        """Get Anthropic API key from environment."""
        return os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY")

    @staticmethod
    def get_llm_provider() -> str:
        """Determine which LLM provider to use based on available API keys."""
        if Config.get_anthropic_api_key():
            return "anthropic"
        elif Config.get_openai_api_key():
            return "openai"
        else:
            raise ValueError(
                "No LLM API key found. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file"
            )

