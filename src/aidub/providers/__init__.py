"""LLM providers package: router, adapters, config, factory, schemas, and validator."""

from aidub.providers.config import ProviderConfig, UnofficialConfig
from aidub.providers.custom_adapter import CustomUrlAdapter
from aidub.providers.deepseek_adapter import DeepSeekAdapter
from aidub.providers.factory import build_router_from_config
from aidub.providers.gemini_adapter import GeminiAdapter
from aidub.providers.openai_adapter import OpenAIAdapter
from aidub.providers.openrouter_adapter import OpenRouterAdapter
from aidub.providers.router import (
    CircuitBreaker,
    CircuitState,
    LlmAdapter,
    LlmProviderError,
    LlmProviderKind,
    LlmProviderRouter,
    LlmRequest,
    LlmResponse,
    LlmRouterConfig,
    _SyntheticLlmAdapter,
)
from aidub.providers.schemas import QCResult, SceneSummary, TranslationResult
from aidub.providers.validator import LlmResponseValidator, ValidationRepairError

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CustomUrlAdapter",
    "DeepSeekAdapter",
    "GeminiAdapter",
    "LlmAdapter",
    "LlmProviderError",
    "LlmProviderKind",
    "LlmProviderRouter",
    "LlmRequest",
    "LlmResponse",
    "LlmResponseValidator",
    "LlmRouterConfig",
    "OpenAIAdapter",
    "OpenRouterAdapter",
    "ProviderConfig",
    "QCResult",
    "SceneSummary",
    "TranslationResult",
    "UnofficialConfig",
    "ValidationRepairError",
    "_SyntheticLlmAdapter",
    "build_router_from_config",
]
