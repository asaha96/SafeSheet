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
    def get_deepseek_api_key() -> Optional[str]:
        """Get DeepSeek API key from environment."""
        return os.getenv("DEEPSEEK_API_KEY")

    @staticmethod
    def get_deepseek_endpoint() -> Optional[str]:
        """Get DeepSeek endpoint URL from environment."""
        return os.getenv("DEEPSEEK_ENDPOINT", "https://aritraintelligence.services.ai.azure.com/openai/v1/")

    @staticmethod
    def get_deepseek_model() -> Optional[str]:
        """Get DeepSeek model name from environment."""
        return os.getenv("DEEPSEEK_MODEL", "DeepSeek-V3.2")

    @staticmethod
    def get_llm_provider() -> str:
        """Determine which LLM provider to use based on available API keys."""
        if Config.get_deepseek_api_key():
            return "deepseek"
        elif Config.get_anthropic_api_key():
            return "anthropic"
        elif Config.get_openai_api_key():
            return "openai"
        else:
            raise ValueError(
                "No LLM API key found. Please set DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env file"
            )

