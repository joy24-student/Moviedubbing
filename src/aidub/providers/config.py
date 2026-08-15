"""Configuration schema and .env loader for LLM providers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from aidub.contracts.base import ContractModel


@dataclass
class UnofficialConfig:
    """Configuration for an unofficial / custom OpenAI-compatible API endpoint."""

    name: str = "custom"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    extra_headers: dict[str, str] = field(default_factory=dict)


class ProviderConfig(ContractModel):
    """
    Multi-provider LLM system configuration.
    
    Loads configuration from environment variables or a `.env` file automatically.
    """

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-001"
    openrouter_site_url: str = ""
    openrouter_app_name: str = "aidub"

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # OpenAI / ChatGPT
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Unofficial / Custom endpoints
    unofficial_configs: list[UnofficialConfig] = field(default_factory=list)

    # Provider priority list (tried in this order)
    provider_priority: list[str] = field(default_factory=lambda: [
        "openrouter", "gemini", "openai", "deepseek", "unofficial"
    ])

    # Agent Loop parameters
    use_agent_loop: bool = True
    agent_max_iterations: int = 20
    agent_quality_threshold: float = 0.80

    @classmethod
    def from_env(cls, env_file: Path | str | None = None) -> ProviderConfig:
        """Create ProviderConfig by reading environment variables (and optional .env file)."""
        if env_file:
            _load_dotenv(Path(env_file))
        else:
            # Try default .env location in current working directory or workspace root
            possible_env = Path(".env")
            if possible_env.exists():
                _load_dotenv(possible_env)

        unofficial_list: list[UnofficialConfig] = []
        # Check for UNOFFICIAL_1_URL, UNOFFICIAL_2_URL, etc.
        idx = 1
        while True:
            prefix = f"UNOFFICIAL_{idx}_"
            url = os.getenv(f"{prefix}URL")
            if not url:
                break
            key = os.getenv(f"{prefix}KEY", "")
            model = os.getenv(f"{prefix}MODEL", "default")
            name = os.getenv(f"{prefix}NAME", f"unofficial_{idx}")
            unofficial_list.append(UnofficialConfig(name=name, api_key=key, base_url=url, model=model))
            idx += 1

        priority_str = os.getenv("PROVIDER_PRIORITY")
        priority = [p.strip().lower() for p in priority_str.split(",")] if priority_str else [
            "openrouter", "gemini", "openai", "deepseek", "unofficial"
        ]

        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            unofficial_configs=unofficial_list,
            provider_priority=priority,
        )


def _load_dotenv(path: Path) -> None:
    """Simple .env file parser."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and not os.getenv(k):
                os.environ[k] = v
    except Exception:
        pass


__all__ = ["ProviderConfig", "UnofficialConfig"]
