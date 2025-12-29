"""LLM utility functions for structured output generation.

This module provides centralized LLM configuration with Pydantic model binding
for type-safe, validated responses across all workflow nodes.
"""

from typing import Type, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import get_settings

T = TypeVar('T', bound=BaseModel)


def get_structured_llm(pydantic_model: Type[T]) -> ChatOpenAI:
    """Get a configured LLM instance with structured output binding.

    This function creates a ChatOpenAI instance configured according to the
    application settings (provider, temperature, max_tokens) and binds it to
    the provided Pydantic model for structured output generation.

    Args:
        pydantic_model: Pydantic model class defining the expected output schema.
            The LLM will be constrained to return responses matching this schema.

    Returns:
        ChatOpenAI: Configured LLM instance ready for invocation.
            Use pattern: `result = llm.invoke(prompt)` where result is an
            instance of `pydantic_model`.

    Raises:
        ValueError: If the LLM provider is invalid or required API keys are missing.

    Examples:
        >>> from backend.src.models.review import Rubric
        >>> llm = get_structured_llm(Rubric)
        >>> result = llm.invoke("Generate a rubric for Senior Backend Engineer")
        >>> assert isinstance(result, Rubric)

        >>> from backend.src.models.memory import WorkingMemory
        >>> llm = get_structured_llm(WorkingMemory)
        >>> result = llm.invoke(prompt)
        >>> assert isinstance(result, WorkingMemory)
    """
    settings = get_settings()

    # Validate provider configuration
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI API key is required when llm_provider='openai'. "
                "Set OPENAI_API_KEY environment variable."
            )

        # Configure OpenAI provider
        llm = ChatOpenAI(
            model=settings.openai_model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )

    elif settings.llm_provider == "llamacpp-server":
        # Configure llama.cpp server provider with OpenAI-compatible API
        llm = ChatOpenAI(
            base_url=settings.llamacpp_base_url,
            api_key=settings.llamacpp_api_key,
            model="local-model",  # Model name is ignored by llama.cpp server
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    else:
        raise ValueError(
            f"Invalid llm_provider: '{settings.llm_provider}'. "
            "Must be 'openai' or 'llamacpp-server'."
        )

    # Bind Pydantic model for structured output
    # This leverages OpenAI's structured output feature for type-safe responses
    structured_llm = llm.with_structured_output(pydantic_model)

    return structured_llm
